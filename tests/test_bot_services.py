import pytest
import os
import json
import asyncio

# Ensure test DB is used
os.environ["SQLITE_DB_PATH"] = "data/test_everest.db"
os.environ["BOT_TOKEN"] = "123456789:TEST_MOCK_TOKEN"
os.environ["BOT_USERNAME"] = "test_everest_bot"

from bot.services.db import db
from bot.services.referral_service import referral_service
from bot.services.test_service import test_service
from bot.services.course_service import course_service
from bot.services.ai_service import ai_service

@pytest.fixture(autouse=True, scope="session")
def setup_test_environment():
    test_db = "data/test_everest.db"
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass
    yield
    if os.path.exists(test_db):
        try:
            os.remove(test_db)
        except Exception:
            pass

@pytest.mark.asyncio
async def test_database_init():
    await db.init()
    # Check default seeded records
    channels = await db.fetch_all("SELECT * FROM required_channels")
    assert len(channels) >= 1
    courses = await db.fetch_all("SELECT * FROM courses")
    assert len(courses) >= 1
    contests = await db.fetch_all("SELECT * FROM contests")
    assert len(contests) >= 1

@pytest.mark.asyncio
async def test_referral_flow_and_anti_fraud():
    # 1. Create inviter
    inviter = await referral_service.get_or_create_user(
        telegram_id=111222,
        full_name="Akmal Karimov",
        username="akmal_dev"
    )
    assert inviter["referral_code"] is not None

    # 2. Invitee joins via referral link
    invitee = await referral_service.get_or_create_user(
        telegram_id=333444,
        full_name="Bobur Aliyev",
        username="bobur_test",
        referred_by_code=inviter["referral_code"]
    )
    assert invitee["referred_by"] == 111222

    # Check pending referral recorded
    ref = await db.fetch_one("SELECT * FROM referrals WHERE invitee_id = 333444")
    assert ref["status"] == "pending"

    # Before phone verification, stats should show 0 points
    stats_before = await referral_service.get_user_stats(111222)
    assert stats_before["confirmed_refs"] == 0

    # 3. Invitee verifies phone number
    await db.execute("UPDATE users SET phone = '+998901234567' WHERE telegram_id = 333444")
    result = await referral_service.confirm_referral_if_eligible(333444)
    assert result is not None
    assert result["inviter_id"] == 111222
    assert result["points"] == 10

    # Check ledger and updated stats
    stats_after = await referral_service.get_user_stats(111222)
    assert stats_after["confirmed_refs"] == 1
    assert stats_after["points"] >= 10

    # 4. Check Leaderboard name masking (Privacy compliance)
    leaderboard = await referral_service.get_leaderboard(limit=5)
    assert len(leaderboard) >= 1
    top_user = next(u for u in leaderboard if u["user_id"] == 111222)
    assert top_user["name"] == "Akmal K."

@pytest.mark.asyncio
async def test_test_management_and_grading():
    # Parse key
    raw_key = "1a 2c 3b 4d 5a"
    parsed = test_service.parse_answer_key(raw_key, 5)
    assert parsed == {1: "A", 2: "C", 3: "B", 4: "D", 5: "A"}

    # Create test
    test = await test_service.create_test(
        teacher_id=111222,
        title="Python Basics Unit Test",
        subject="Python",
        question_count=5,
        answer_key=parsed,
        time_limit=15
    )
    assert test["code"].startswith("EV-")

    # Start student attempt
    attempt, msg = await test_service.start_attempt(test["id"], user_id=333444)
    assert attempt is not None

    # Save answers (3 correct, 2 wrong)
    await test_service.save_answer(attempt["id"], 1, "A") # correct
    await test_service.save_answer(attempt["id"], 2, "C") # correct
    await test_service.save_answer(attempt["id"], 3, "B") # correct
    await test_service.save_answer(attempt["id"], 4, "A") # wrong (correct is D)
    await test_service.save_answer(attempt["id"], 5, "B") # wrong (correct is A)

    # Finish and verify grading
    result = await test_service.finish_attempt(attempt["id"])
    assert result["correct_count"] == 3
    assert result["total_questions"] == 5
    assert result["percentage"] == 60.0
    assert result["score"] == 6

    # Verify Excel report generation
    excel_bytes = await test_service.generate_excel_report(test["id"])
    assert len(excel_bytes) > 1000 # Valid xlsx file

@pytest.mark.asyncio
async def test_course_enrollment():
    categories = await course_service.get_categories()
    assert len(categories) >= 1

    courses = await course_service.get_courses_by_category(categories[0])
    assert len(courses) >= 1
    course = courses[0]

    # Submit enrollment
    enrollment = await course_service.create_enrollment(
        course_id=course["id"],
        user_id=333444,
        name="Bobur Aliyev",
        phone="+998901234567",
        age=20,
        preferred_time="Kechki 18:30"
    )
    assert enrollment["status"] == "yangi"

    # Check duplicate prevention
    has_active = await course_service.check_active_enrollment(course["id"], 333444)
    assert has_active is True

@pytest.mark.asyncio
async def test_ai_service_fallback():
    variants = await ai_service.generate_channel_posts("Kiberxavfsizlik va dasturlash")
    assert len(variants) >= 3
    for v in variants:
        assert len(v) > 50
        assert "Everest IT Center" in v
