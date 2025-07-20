from typing import Optional

from django.db.models import Count
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Q
from django.utils import timezone
from ninja import Query
from ninja import Router

from content.models import Comment
from content.models import Follow
from content.models import Impression
from content.models import Like
from content.models import Post
from content.models import Save
from content.models import Share
from content.schemas import CommentCreateSchema
from content.schemas import CommentSchema
from content.schemas import FeedExcludeSchema
from content.schemas import PaginatedPostsSchema
from content.schemas import PostSchema
from content.schemas import ShareCreateSchema
from content.schemas import ShareResponseSchema
from users.auth import JWTAuth
from users.models import User

auth = JWTAuth()
content_router = Router(tags=["Feeds and Interactions"])


def _get_post_with_interactions(user: User, post_qs):
    # Annotate counts
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
        author_id=post.author.id,
        author_username=post.author.username,
        media_url=post.media_url,
        caption=post.caption,
        themes=[t.name for t in post.themes.all()],
        created_at=post.created_at,
        likes_count=getattr(post, "likes_count", 0),
        comments_count=getattr(post, "comments_count", 0),
        saves_count=getattr(post, "saves_count", 0),
        shares_count=getattr(post, "shares_count", 0),
        liked=getattr(post, "liked", False),
        saved=getattr(post, "saved", False),
    )


@content_router.get("/feeds/foryou/", response=Optional[PostSchema], auth=auth)
def feed_for_you(request, exclude_ids: Optional[list[int]] = Query(None)):
    user = request.auth
    # Base queryset excludes own posts and excludes exclude_ids if given
    base_qs = Post.objects.exclude(author=user)
    if exclude_ids:
        base_qs = base_qs.exclude(id__in=exclude_ids)

    # Filter by similar body_type & overlapping themes (must have at least one matching theme)
    theme_ids = list(user.themes.values_list("id", flat=True))
    similar_body_type = user.body_type
    similar_height = user.height
    similar_weight = user.weight

    # Filter posts whose author matches user on body_type, height±5, weight±5, and shares at least one theme
    filtered_qs = base_qs.filter(
        author__body_type=similar_body_type,
        author__height__gte=similar_height - 5,
        author__height__lte=similar_height + 5,
        author__weight__gte=similar_weight - 5,
        author__weight__lte=similar_weight + 5,
        themes__id__in=theme_ids,
    ).distinct()

    qs = _get_post_with_interactions(user, filtered_qs)
    # Random order, pick one or None
    post = qs.order_by("?").first()

    if post:
        # Log impression
        Impression.objects.create(user=user, post=post)
        return _serialize_post(user, post)
    return None


@content_router.get(
    "/feeds/friends/", response=Optional[PostSchema], auth=auth
)
def feed_friends(request, exclude_ids: Optional[list[int]] = Query(None)):
    user = request.auth
    following_ids = Follow.objects.filter(follower=user).values_list(
        "following_id", flat=True
    )
    qs = Post.objects.filter(author_id__in=following_ids)
    if exclude_ids:
        qs = qs.exclude(id__in=exclude_ids)

    qs = _get_post_with_interactions(user, qs)
    post = qs.order_by("?").first()
    if post:
        Impression.objects.create(user=user, post=post)
        return _serialize_post(user, post)
    return None


@content_router.get(
    "/feeds/explore/", response=Optional[PostSchema], auth=auth
)
def feed_explore(request, exclude_ids: Optional[list[int]] = Query(None)):
    user = request.auth
    following_ids = set(
        Follow.objects.filter(follower=user).values_list(
            "following_id", flat=True
        )
    )
    user_theme_ids = set(user.themes.values_list("id", flat=True))

    base_qs = Post.objects.exclude(author=user)
    if exclude_ids:
        base_qs = base_qs.exclude(id__in=exclude_ids)

    # Exclude posts from users you follow and posts that share user's themes
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
    return None


@content_router.get("/feeds/upload/", response=PaginatedPostsSchema, auth=auth)
def feed_upload(
    request, offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=50)
):
    user = request.auth
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
def like_post(request, post_id: int):
    user = request.auth
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return {"error": "Post not found"}

    like, created = Like.objects.get_or_create(user=user, post=post)
    if not created:
        # Already liked → unlike (toggle)
        like.delete()
        return {"liked": False}
    return {"liked": True}


@content_router.post("/interactions/save/", auth=auth)
def save_post(request, post_id: int):
    user = request.user
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return {"error": "Post not found"}

    save, created = Save.objects.get_or_create(user=user, post=post)
    if not created:
        # Already saved → unsave (toggle)
        save.delete()
        return {"saved": False}
    return {"saved": True}


@content_router.post(
    "/interactions/comment/", response=CommentSchema, auth=auth
)
def comment_post(request, payload: CommentCreateSchema):
    user = request.user
    post = Post.objects.filter(id=payload.post_id).first()
    if not post:
        return {"error": "Post not found"}

    comment = Comment.objects.create(user=user, post=post, text=payload.text)
    return CommentSchema(
        id=comment.id,
        user_id=user.id,
        username=user.username,
        text=comment.text,
        created_at=comment.created_at,
    )


@content_router.post(
    "/interactions/share/", response=ShareResponseSchema, auth=auth
)
def share_post(request, payload: ShareCreateSchema):
    user = request.user
    post = Post.objects.filter(id=payload.post_id).first()
    if not post:
        return {"error": "Post not found"}

    share = Share(user=user, post=post)
    share.save()  # slug auto-generated
    return ShareResponseSchema(slug=share.slug)


@content_router.get("/share/{slug}/")
def track_share_click(request, slug: str):
    share = (
        Share.objects.filter(slug=slug).select_related("post", "user").first()
    )
    if not share:
        return {"error": "Invalid share link"}

    # Optionally, increment a click counter here or log click event

    return {
        "post_id": share.post.id,
        "shared_by_user_id": share.user.id,
        "media_url": share.post.media_url,
        "caption": share.post.caption,
    }
