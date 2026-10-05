import json
import logging
from typing import Optional, Dict, Any, List
from bot.services.db import db

logger = logging.getLogger(__name__)

class CourseService:
    @staticmethod
    async def get_categories() -> List[str]:
        rows = await db.fetch_all("SELECT DISTINCT category FROM courses WHERE status = 'published'")
        return [r["category"] for r in rows if r.get("category")]

    @staticmethod
    async def get_courses_by_category(category: str) -> List[Dict[str, Any]]:
        return await db.fetch_all("SELECT * FROM courses WHERE category = ? AND status = 'published'", (category,))

    @staticmethod
    async def get_course_by_id(course_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT c.*, u.full_name as teacher_name
            FROM courses c
            LEFT JOIN users u ON u.telegram_id = c.teacher_id
            WHERE c.id = ?
        """
        return await db.fetch_one(query, (course_id,))

    @staticmethod
    async def check_active_enrollment(course_id: int, user_id: int) -> bool:
        """Prevent spamming multiple active applications to same course."""
        existing = await db.fetch_one("""
            SELECT id FROM course_enrollments 
            WHERE course_id = ? AND user_id = ? AND status IN ('yangi', 'boglanildi')
        """, (course_id, user_id))
        return bool(existing)

    @staticmethod
    async def create_enrollment(
        course_id: int,
        user_id: int,
        name: str,
        phone: str,
        age: Optional[int] = None,
        preferred_time: Optional[str] = None,
        note: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create new enrollment application and return data for notifications."""
        await db.execute("""
            INSERT INTO course_enrollments (
                course_id, user_id, name, phone, age, preferred_time, note, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'yangi')
        """, (course_id, user_id, name, phone, age, preferred_time, note))

        enrollment = await db.fetch_one("""
            SELECT e.*, c.title as course_title, c.teacher_id
            FROM course_enrollments e
            JOIN courses c ON c.id = e.course_id
            WHERE e.course_id = ? AND e.user_id = ?
            ORDER BY e.id DESC LIMIT 1
        """, (course_id, user_id))

        return enrollment

    @staticmethod
    async def get_teacher_enrollments(teacher_id: int, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch applications for teacher's courses."""
        if status:
            query = """
                SELECT e.*, c.title as course_title, u.username
                FROM course_enrollments e
                JOIN courses c ON c.id = e.course_id
                JOIN users u ON u.telegram_id = e.user_id
                WHERE c.teacher_id = ? AND e.status = ?
                ORDER BY e.created_at DESC
            """
            return await db.fetch_all(query, (teacher_id, status))
        else:
            query = """
                SELECT e.*, c.title as course_title, u.username
                FROM course_enrollments e
                JOIN courses c ON c.id = e.course_id
                JOIN users u ON u.telegram_id = e.user_id
                WHERE c.teacher_id = ?
                ORDER BY e.created_at DESC
            """
            return await db.fetch_all(query, (teacher_id,))

    @staticmethod
    async def update_enrollment_status(enrollment_id: int, new_status: str, teacher_note: Optional[str] = None) -> None:
        if new_status == "boglanildi":
            await db.execute("""
                UPDATE course_enrollments 
                SET status = ?, teacher_note = COALESCE(?, teacher_note), contacted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, teacher_note, enrollment_id))
        else:
            await db.execute("""
                UPDATE course_enrollments 
                SET status = ?, teacher_note = COALESCE(?, teacher_note), updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_status, teacher_note, enrollment_id))

course_service = CourseService()
