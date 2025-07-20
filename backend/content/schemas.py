from datetime import datetime
from typing import Optional

from ninja import Schema


class PostSchema(Schema):
    id: int
    author_id: int
    author_username: Optional[str]
    media_url: str
    caption: Optional[str]
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
    user_id: int
    username: Optional[str]
    text: str
    created_at: datetime


class ShareCreateSchema(Schema):
    post_id: int


class ShareResponseSchema(Schema):
    slug: str


class FeedExcludeSchema(Schema):
    exclude_ids: Optional[list[int]] = None


class PaginatedPostsSchema(Schema):
    posts: list[PostSchema]
    total: int
    offset: int
    limit: int
