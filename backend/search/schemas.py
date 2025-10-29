from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    username: str | None
    full_name: str | None
    bio: str | None


class PostOut(BaseModel):
    post_id: int
    author_id: str
    author_username: str | None
    caption: str | None
    themes: list[str]
