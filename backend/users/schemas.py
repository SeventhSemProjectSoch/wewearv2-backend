import uuid

from ninja import ModelSchema, Schema
from users.models import Theme


class ThemeModelSchema(ModelSchema):
    class Meta:
        model = Theme
        exclude = ["id"]


class ProfileSchema(Schema):
    id: uuid.UUID
    username: str | None = None
    full_name: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    body_type: str | None = None
    height: float | None = None
    weight: float | None = None
    gender: str | None = None
    themes: list[str]
    followers_count: int
    following_count: int
    posts_count: int
    is_following: bool = False


class UpdateProfileSchema(Schema):
    username: str | None = None
    full_name: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    body_type: str | None = None
    height: float | None = None
    weight: float | None = None
    gender: str | None = None
    themes: list[str] = []


class RequestOTPSchema(Schema):
    email: str


class VerifyOTPSchema(Schema):
    email: str | None = None
    code: str


class TokenSchema(Schema):
    access_token: str
    token_type: str = "bearer"


class ExistsSchema(Schema):
    exists: bool
    email: str
