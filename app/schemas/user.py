import uuid
from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    profile_picture: Optional[str] = None

    model_config = {"from_attributes": True}
