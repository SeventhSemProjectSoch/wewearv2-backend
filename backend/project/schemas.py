from ninja import Schema


class GenericResponse(Schema):
    error: str | None = None
    detail: str | None = None
