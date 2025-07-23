from typing import cast

from django.db import transaction
from django.db.models import Count
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Router
from ninja.errors import ValidationError

from content.models import Comment
from content.models import Follow
from content.models import Impression
from content.models import Like
from content.models import Post
from content.models import Save
from content.models import Share
from content.schemas import CommentCreateSchema
from content.schemas import CommentSchema
from content.schemas import PaginatedPostsSchema
from content.schemas import PostCreateSchema
from content.schemas import PostSchema
from content.schemas import ShareCreateSchema
from content.schemas import ShareResponseSchema
from project.schemas import GenericResponse
from users.auth import JWTAuth
from users.models import Theme
from users.models import User

auth = JWTAuth()
content_router = Router(tags=["Feeds and Interactions"])


def _get_post_with_interactions(user: User, post_qs: QuerySet[Post, Post]):
    qs = post_qs.annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
        saves_count=Count("saves", distinct=True),
        shares_count=Count("shares", distinct=True),
        liked=Exists(Like.objects.filter(user=user, post=OuterRef("pk"))),
        saved=Exists(Save.objects.filter(user=user, post=OuterRef("pk"))),
    )
    return qs


def _serialize_post(user: User, post: Post) -> PostSchema:
    return PostSchema(
        id=post.id,
        author_id=str(post.author.id),
        author_username=post.author.username,
        media_url=post.media(),
        caption=post.caption,
        themes=[theme.name for theme in post.themes.all()],
        created_at=post.created_at,
        likes_count=getattr(post, "likes_count", 0),
        comments_count=getattr(post, "comments_count", 0),
        saves_count=getattr(post, "saves_count", 0),
        shares_count=getattr(post, "shares_count", 0),
        liked=getattr(post, "liked", False),
        saved=getattr(post, "saved", False),
    )


@content_router.get(
    "/feeds/foryou/", response=PostSchema | GenericResponse, auth=auth
)
def feed_for_you(request: HttpRequest):
    user = cast(User, request.user)

    base_qs = Post.objects.exclude(author=user)

    # FIXME: add user blocking, so blocked user content dosenot appear here
    # base_qs = base_qs.exclude(id__in=exclude_ids)

    theme_ids = list(user.themes.values_list("id", flat=True))
    similar_body_type = user.body_type
    similar_height = user.height
    similar_weight = user.weight

    if similar_height:
        base_qs = base_qs.filter(
            author__height__gte=similar_height - 5,
            author__height__lte=similar_height + 5,
        )

    if similar_weight:
        base_qs = base_qs.filter(
            author__weight__gte=similar_weight - 5,
            author__weight__lte=similar_weight + 5,
        )

    if similar_body_type:
        base_qs = base_qs.filter(
            author__body_type=similar_body_type,
        )
    if theme_ids:
        base_qs = base_qs.filter(
            themes__id__in=theme_ids,
        )

    # base_qs = base_qs.exclude(
    #     Exists(Impression.objects.filter(user=user, post=OuterRef("pk")))
    # )
    filtered_qs = base_qs.distinct()

    qs = _get_post_with_interactions(user, filtered_qs)

    post = qs.order_by("?").first()

    if post:
        Impression.objects.create(user=user, post=post)
        return _serialize_post(user, post)
    return GenericResponse(detail="You have reached the end of content.")


@content_router.get(
    "/feeds/friends/", response=PostSchema | GenericResponse, auth=auth
)
def feed_friends(request: HttpRequest):
    user = cast(User, request.user)
    following_ids = Follow.objects.filter(follower=user).values_list(
        "following_id", flat=True
    )
    qs = Post.objects.filter(author_id__in=following_ids)
    qs = qs.exclude(
        Exists(Impression.objects.filter(user=user, post=OuterRef("pk")))
    )
    qs = _get_post_with_interactions(user, qs)
    post = qs.order_by("?").first()
    if post:
        Impression.objects.create(user=user, post=post)
        return _serialize_post(user, post)
    return GenericResponse(detail="You have reached the end of content.")


@content_router.get(
    "/feeds/explore/", response=PostSchema | GenericResponse, auth=auth
)
def feed_explore(request: HttpRequest):
    user = cast(User, request.user)
    following_ids = set(
        Follow.objects.filter(follower=user).values_list(
            "following_id", flat=True
        )
    )
    user_theme_ids = set(user.themes.values_list("id", flat=True))

    base_qs = Post.objects.exclude(author=user)
    base_qs = base_qs.exclude(
        Exists(Impression.objects.filter(user=user, post=OuterRef("pk")))
    )
    filtered_qs = (
        base_qs.exclude(author_id__in=following_ids)
        .exclude(themes__id__in=user_theme_ids)
        .distinct()
    )

    qs = _get_post_with_interactions(user, filtered_qs)
    post = qs.order_by("?").first()
    if post:
        Impression.objects.create(user=user, post=post)
        return _serialize_post(user, post)
    return GenericResponse(detail="You have reached the end of content.")


@content_router.get("/feeds/upload/", response=PaginatedPostsSchema, auth=auth)
def feed_upload(
    request: HttpRequest,
    offset: int = 0,
    limit: int = 20,
):
    user = cast(User, request.user)
    qs = Post.objects.filter(author=user).order_by("-created_at")
    total = qs.count()
    posts = qs[offset : offset + limit]
    posts = _get_post_with_interactions(user, posts)
    posts = list(posts)
    serialized_posts = [_serialize_post(user, p) for p in posts]

    return PaginatedPostsSchema(
        posts=serialized_posts, total=total, offset=offset, limit=limit
    )


@content_router.post("/interactions/like/", auth=auth)
def like_post(request: HttpRequest, post_id: int):
    user = cast(User, request.user)
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return {"error": "Post not found"}

    like, created = Like.objects.get_or_create(user=user, post=post)
    if not created:
        like.delete()
        return {"liked": False}
    return {"liked": True}


@content_router.post("/interactions/save/", auth=auth)
def save_post(request: HttpRequest, post_id: int):
    user = cast(User, request.user)
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return {"error": "Post not found"}

    save, created = Save.objects.get_or_create(user=user, post=post)
    if not created:
        save.delete()
        return {"saved": False}
    return {"saved": True}


@content_router.post(
    "/interactions/comment/", response=CommentSchema, auth=auth
)
def comment_post(request: HttpRequest, payload: CommentCreateSchema):
    user = cast(User, request.user)
    post = Post.objects.filter(id=payload.post_id).first()
    if not post:
        return {"error": "Post not found"}

    comment = Comment.objects.create(user=user, post=post, text=payload.text)
    return CommentSchema(
        id=comment.id,
        user_id=str(user.id),
        username=(user.username or ""),
        text=comment.text,
        created_at=comment.created_at,
    )


@content_router.post(
    "/interactions/share/", response=ShareResponseSchema, auth=auth
)
def share_post(request: HttpRequest, payload: ShareCreateSchema):
    user = cast(User, request.user)
    post = Post.objects.filter(id=payload.post_id).first()
    if not post:
        return {"error": "Post not found"}

    share = Share(user=user, post=post)
    share.save()
    return ShareResponseSchema(slug=share.slug)


@content_router.get("/share/{slug}/")
def track_share_click(request: HttpRequest, slug: str):
    share = (
        Share.objects.filter(slug=slug).select_related("post", "user").first()
    )
    if not share:
        return {"error": "Invalid share link"}

    return {
        "post_id": share.post.id,
        "shared_by_user_id": share.user.id,
        "media_url": share.post.media_url,
        "caption": share.post.caption,
    }


@content_router.post("/posts/", auth=auth)
def create_post(request: HttpRequest, post: PostCreateSchema):
    user = cast(User, request.user)

    if not post.media_url and not post.media_file:
        raise ValidationError(
            [
                {
                    "Must provide either post url or file": "Either media_url or media_file must be provided"
                }
            ]
        )

    with transaction.atomic():
        post_obj = Post(author=user, caption=post.caption)

        if post.media_file:
            post_obj.media_file = post.media_file
        elif post.media_url:
            post_obj.media_url = post.media_url

        post_obj.save()

        post_obj.themes.set(
            [
                Theme.objects.get_or_create(name=theme_name)[0]
                for theme_name in post.themes
            ]
        )

    return {
        "id": post_obj.id,
        "media": post_obj.media(),
        "caption": post_obj.caption,
    }
