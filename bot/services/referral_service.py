import secrets
import string
import logging
from typing import Optional, Dict, Any, List
from bot.services.db import db
from bot.config import settings

logger = logging.getLogger(__name__)

class ReferralService:
    @staticmethod
    def generate_referral_code(length: int = 8) -> str:
        """Generate a random 8-character alphanumeric referral code."""
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    async def get_or_create_user(
        telegram_id: int,
        full_name: str,
        username: Optional[str] = None,
        referred_by_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fetch existing user or create a new user with referral tracking."""
        user = await db.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        if user:
            return user

        # Resolve inviter if referral code is given
        inviter_id = None
        if referred_by_code:
            inviter = await db.fetch_one("SELECT telegram_id FROM users WHERE referral_code = ?", (referred_by_code,))
            if inviter and inviter["telegram_id"] != telegram_id:
                inviter_id = inviter["telegram_id"]

        # Generate unique referral code for the new user
        code = ReferralService.generate_referral_code()
        while await db.fetch_one("SELECT id FROM users WHERE referral_code = ?", (code,)):
            code = ReferralService.generate_referral_code()

        # Check if user is superadmin
        role = "superadmin" if telegram_id in settings.superadmin_list else "user"

        await db.execute("""
            INSERT INTO users (telegram_id, full_name, username, role, referral_code, referred_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (telegram_id, full_name, username, role, code, inviter_id))

        new_user = await db.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))

        # If there's an inviter, register pending referral
        if inviter_id:
            # Active contest if any
            active_contest = await db.fetch_one("SELECT id FROM contests WHERE status = 'active' ORDER BY id DESC LIMIT 1")
            contest_id = active_contest["id"] if active_contest else None

            # Create pending referral entry
            await db.execute("""
                INSERT INTO referrals (inviter_id, invitee_id, contest_id, status)
                VALUES (?, ?, ?, 'pending')
            """, (inviter_id, telegram_id, contest_id))

        return new_user

    @staticmethod
    async def confirm_referral_if_eligible(telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Anti-fraud check: Once invitee joins mandatory channel and confirms phone,
        grant points to inviter and log to points_ledger.
        """
        user = await db.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        if not user or not user.get("phone") or not user.get("referred_by"):
            return None

        # Check pending referral record
        ref = await db.fetch_one("""
            SELECT * FROM referrals 
            WHERE invitee_id = ? AND status = 'pending'
        """, (telegram_id,))
        if not ref:
            return None

        inviter_id = ref["inviter_id"]
        contest_id = ref.get("contest_id")

        # Anti-fraud velocity check: count referrals in last 1 hour
        recent_count = await db.fetch_val("""
            SELECT COUNT(*) FROM referrals 
            WHERE inviter_id = ? AND created_at >= datetime('now', '-1 hour')
        """, (inviter_id,)) or 0

        # If more than 30 referrals in 1 hour, flag as suspicious
        if recent_count > 30:
            await db.execute("""
                UPDATE referrals 
                SET status = 'flagged', flag_reason = 'Juda tez takliflar oqimi (>30/soat)'
                WHERE id = ?
            """, (ref["id"],))
            return None

        # Get point amount setting
        setting_val = await db.fetch_val("SELECT value FROM settings WHERE key = 'referral_points'")
        points = int(setting_val) if setting_val and str(setting_val).isdigit() else settings.DEFAULT_REFERRAL_POINTS

        # Update referral to confirmed
        await db.execute("""
            UPDATE referrals 
            SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (ref["id"],))

        # Add points to immutable ledger
        await db.execute("""
            INSERT INTO points_ledger (user_id, contest_id, amount, source, reference_id, reason)
            VALUES (?, ?, ?, 'referral', ?, ?)
        """, (inviter_id, contest_id, points, str(ref["id"]), f"Do'st taklifi: {user.get('full_name')}"))

        return {
            "inviter_id": inviter_id,
            "points": points,
            "friend_name": user.get("full_name")
        }

    @staticmethod
    async def get_user_stats(telegram_id: int, contest_id: Optional[int] = None) -> Dict[str, Any]:
        """Fetch total points, total referrals, confirmed and pending count."""
        # Total points in contest or all-time
        if contest_id:
            points = await db.fetch_val("""
                SELECT COALESCE(SUM(amount), 0) FROM points_ledger 
                WHERE user_id = ? AND contest_id = ?
            """, (telegram_id, contest_id)) or 0
        else:
            points = await db.fetch_val("""
                SELECT COALESCE(SUM(amount), 0) FROM points_ledger 
                WHERE user_id = ?
            """, (telegram_id,)) or 0

        total_refs = await db.fetch_val("SELECT COUNT(*) FROM referrals WHERE inviter_id = ?", (telegram_id,)) or 0
        confirmed_refs = await db.fetch_val("SELECT COUNT(*) FROM referrals WHERE inviter_id = ? AND status = 'confirmed'", (telegram_id,)) or 0
        pending_refs = await db.fetch_val("SELECT COUNT(*) FROM referrals WHERE inviter_id = ? AND status = 'pending'", (telegram_id,)) or 0

        return {
            "points": points,
            "total_refs": total_refs,
            "confirmed_refs": confirmed_refs,
            "pending_refs": pending_refs
        }

    @staticmethod
    async def get_leaderboard(contest_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top N leaderboard with masked user names."""
        if contest_id:
            query = """
                SELECT p.user_id, u.full_name, SUM(p.amount) as total_points
                FROM points_ledger p
                JOIN users u ON u.telegram_id = p.user_id
                WHERE p.contest_id = ?
                GROUP BY p.user_id, u.full_name
                ORDER BY total_points DESC
                LIMIT ?
            """
            rows = await db.fetch_all(query, (contest_id, limit))
        else:
            query = """
                SELECT p.user_id, u.full_name, SUM(p.amount) as total_points
                FROM points_ledger p
                JOIN users u ON u.telegram_id = p.user_id
                GROUP BY p.user_id, u.full_name
                ORDER BY total_points DESC
                LIMIT ?
            """
            rows = await db.fetch_all(query, (limit,))

        # Mask names (e.g. "Ali V." or "Alisher N***")
        result = []
        for r in rows:
            name_parts = (r.get("full_name") or "Foydalanuvchi").split()
            if len(name_parts) >= 2:
                masked_name = f"{name_parts[0]} {name_parts[1][0]}."
            else:
                masked_name = name_parts[0]
            result.append({
                "user_id": r["user_id"],
                "name": masked_name,
                "points": r["total_points"]
            })
        return result

    @staticmethod
    async def get_user_rank(telegram_id: int, contest_id: Optional[int] = None) -> int:
        """Calculate user's current rank."""
        if contest_id:
            user_pts = await db.fetch_val("""
                SELECT COALESCE(SUM(amount), 0) FROM points_ledger 
                WHERE user_id = ? AND contest_id = ?
            """, (telegram_id, contest_id)) or 0

            higher_count = await db.fetch_val("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, SUM(amount) as s 
                    FROM points_ledger 
                    WHERE contest_id = ? 
                    GROUP BY user_id 
                    HAVING s > ?
                )
            """, (contest_id, user_pts)) or 0
        else:
            user_pts = await db.fetch_val("""
                SELECT COALESCE(SUM(amount), 0) FROM points_ledger 
                WHERE user_id = ?
            """, (telegram_id,)) or 0

            higher_count = await db.fetch_val("""
                SELECT COUNT(*) FROM (
                    SELECT user_id, SUM(amount) as s 
                    FROM points_ledger 
                    GROUP BY user_id 
                    HAVING s > ?
                )
            """, (user_pts,)) or 0

        return higher_count + 1

referral_service = ReferralService()
