from datetime import datetime

from ninja import Schema


class PostSchema(Schema):
    id: int
    author_id: str
    author_username: str | None
    media_url: str | None
    caption: str | None
    themes: list[str]
    created_at: datetime

    likes_count: int
    comments_count: int
    saves_count: int
    shares_count: int

    liked: bool
    saved: bool


class CommentCreateSchema(Schema):
    post_id: int
    text: str


class CommentSchema(Schema):
    id: int
    user_id: str
    username: str
    text: str
    created_at: datetime


class ShareCreateSchema(Schema):
    post_id: int


class ShareResponseSchema(Schema):
    slug: str


class PaginatedPostsSchema(Schema):
    posts: list[PostSchema]
    total: int
    offset: int
    limit: int


class PaginatedCommentsSchema(Schema):
    comments: list[CommentSchema]
    total: int
    offset: int
    limit: int
