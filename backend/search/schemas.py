from pydantic import BaseModel


class UserOut(BaseModel):
    id: str
    username: str | None
    full_name: str | None
    bio: str | None


class PostOut(BaseModel):
    id: int
    author_id: str
    author_username: str | None
    caption: str | None
    themes: list[str]


class ThemeOut(BaseModel):
    id: int
    name: str


class SearchUsersQuery(BaseModel):
    q: str
    limit: int | None = 20
    offset: int | None = 0


class SearchPostsQuery(BaseModel):
    q: str
    limit: int | None = 20
    offset: int | None = 0


class SearchThemesQuery(BaseModel):
    q: str
    used_only: bool | None = False
    limit: int | None = 20
    offset: int | None = 0
