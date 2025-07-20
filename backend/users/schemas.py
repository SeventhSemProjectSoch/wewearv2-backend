from ninja import Schema


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
