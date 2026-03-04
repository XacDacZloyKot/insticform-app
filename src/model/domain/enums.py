import enum


class MediaType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class GradingMethod(str, enum.Enum):
    AUTO = "auto"
    MANUAL = "manual"
    MIXED = "mixed"


class QuestionType(str, enum.Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_ANSWER = "text_answer"


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"


class ProctoringAction(str, enum.Enum):
    TAB_SWITCH = "tab_switch"
    COPY_PASTE = "copy_paste"
    MOUSE_LEAVE = "mouse_leave"
    CONNECTION_LOST = "connection_lost"
