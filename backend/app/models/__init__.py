"""Import every model so ``Base.metadata`` and Alembic autogenerate see them."""

from app.models.audit_log import AuditLog
from app.models.exam import Exam
from app.models.notification import Notification
from app.models.password_reset import PasswordResetToken
from app.models.permission import Permission
from app.models.profile import StudentProfile
from app.models.question import Question, QuestionOption
from app.models.role import Role, RolePermission
from app.models.setting import Setting
from app.models.subject import Subject
from app.models.topic import Topic
from app.models.user import User, UserRole

__all__ = [
    "AuditLog",
    "Exam",
    "Notification",
    "Permission",
    "PasswordResetToken",
    "Question",
    "QuestionOption",
    "Role",
    "RolePermission",
    "Setting",
    "StudentProfile",
    "Subject",
    "Topic",
    "User",
    "UserRole",
]
