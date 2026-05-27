# Import every model here so SQLAlchemy registers them all in the mapper registry
# before the first request is handled.  Without these imports the string-based
# relationship references (e.g. "Attendance" in Employee.attendances) cannot be
# resolved and raise InvalidRequestError at runtime.

from app.models.attendance import Attendance  # noqa: F401
from app.models.chat import Chat  # noqa: F401
from app.models.chat_message import ChatMessage  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.employee import Employee  # noqa: F401
from app.models.leave import Leave  # noqa: F401
from app.models.mixins import TimestampSoftDeleteMixin  # noqa: F401
from app.models.payroll import Payroll  # noqa: F401
from app.models.performance import Performance  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.user import User  # noqa: F401
