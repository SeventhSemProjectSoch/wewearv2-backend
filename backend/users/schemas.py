from ninja import Schema


class ProfileSchema(Schema):
    username: str | None = None
    full_name: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    body_type: str | None = None
    height: float | None = None
    weight: float | None = None
    themes: list[str]


class UpdateProfileSchema(Schema):
    username: str
    full_name: str | None = None
    bio: str | None = None
    profile_picture: str | None = None
    body_type: str | None = None
    height: float | None = None
    weight: float | None = None
    themes: list[str]


class RequestOTPSchema(Schema):
    email: str | None = None
    phone: str | None = None


class VerifyOTPSchema(Schema):
    email: str | None = None
    phone: str | None = None
    code: str


class TokenSchema(Schema):
    access_token: str
    token_type: str = "bearer"
