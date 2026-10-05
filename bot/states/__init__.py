from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    choosing_language = State()
    privacy_consent = State()
    waiting_channel_sub = State()
    waiting_phone = State()

class StudentTestStates(StatesGroup):
    entering_code = State()
    taking_test = State()

class TeacherTestStates(StatesGroup):
    waiting_title = State()
    waiting_subject = State()
    waiting_question_count = State()
    waiting_options_count = State()
    waiting_answer_key = State()
    waiting_file = State()
    waiting_time_limit = State()
    confirm_creation = State()

class CourseEnrollStates(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_time = State()
    waiting_note = State()
    confirm_enroll = State()

class TeacherCourseStates(StatesGroup):
    waiting_title = State()
    waiting_category = State()
    waiting_description = State()
    waiting_level = State()
    waiting_price = State()
    waiting_duration = State()
    waiting_schedule = State()
    waiting_format = State()
    waiting_address = State()
    confirm_course = State()

class AIPostStates(StatesGroup):
    waiting_topic = State()
    waiting_target = State()
    waiting_tone = State()
    generating = State()
    review_variants = State()
    editing_variant = State()
    waiting_media = State()
    confirm_publish = State()
    schedule_time = State()

class AdminBroadcastStates(StatesGroup):
    waiting_segment = State()
    waiting_content = State()
    confirm_send = State()

class AdminPointsStates(StatesGroup):
    waiting_user_id = State()
    waiting_amount = State()
    waiting_reason = State()
