from typing import cast

from django.db import transaction
from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.http import HttpRequest
from django.utils import timezone
from ninja import File, Form, Router, UploadedFile
from ninja.errors import ValidationError

from content.models import Comment, Follow, Impression, Like, Post, Save, Share
from content.schemas import (
    CommentCreateSchema,
    CommentSchema,
    PaginatedCommentsSchema,
    PaginatedPostsSchema,
    PostSchema,
    ShareCreateSchema,
    ShareResponseSchema,
)
from project.schemas import GenericResponse
from users.auth import JWTAuth
from users.models import Theme, User
from utils.video import process_post_video_async

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


@content_router.get("/feeds/foryou/", response=PostSchema | GenericResponse, auth=auth)
def feed_for_you(request: HttpRequest):
    user = cast(User, request.user)
    base_qs = Post.objects.exclude(author=user).filter(author__gender=user.gender)
    user_theme_ids = list(user.themes.values_list("id", flat=True))
    similar_body_type = user.body_type
    similar_height = user.height
    similar_weight = user.weight
    score_annotations = {}

    if user_theme_ids:
        score_annotations["theme_match"] = Count(
            "themes", filter=Q(themes__id__in=user_theme_ids), distinct=True
        )
    else:
        score_annotations["theme_match"] = Value(0, output_field=IntegerField())

    if similar_body_type:
        score_annotations["body_type_match"] = Case(
            When(author__body_type=similar_body_type, then=1000),
            default=0,
            output_field=IntegerField(),
        )
    else:
        score_annotations["body_type_match"] = Value(0, output_field=IntegerField())

    if similar_height:
        score_annotations["height_match"] = Case(
            When(
                author__height__gte=similar_height - 30,
                author__height__lte=similar_height + 30,
                then=100,
            ),
            default=0,
            output_field=IntegerField(),
        )
    else:
        score_annotations["height_match"] = Value(0, output_field=IntegerField())

    if similar_weight:
        score_annotations["weight_match"] = Case(
            When(
                author__weight__gte=similar_weight - 15,
                author__weight__lte=similar_weight + 15,
                then=50,
            ),
            default=0,
            output_field=IntegerField(),
        )
    else:
        score_annotations["weight_match"] = Value(0, output_field=IntegerField())

    score_annotations["likes_count"] = Count("likes", distinct=True)
    score_annotations["comments_count"] = Count("comments", distinct=True)
    score_annotations["shares_count"] = Count("shares", distinct=True)
    score_annotations["saves_count"] = Count("saves", distinct=True)

    impression_subquery = Impression.objects.filter(
        user=user, post=OuterRef("pk")
    ).values("viewed_at")[:1]

    filtered_qs = (
        base_qs.annotate(**score_annotations)
        .annotate(
            last_impression=Subquery(impression_subquery),
            has_impression=Exists(
                Impression.objects.filter(user=user, post=OuterRef("pk"))
            ),
            content_score=(
                F("theme_match") * 10
                + F("body_type_match")
                + F("height_match")
                + F("weight_match")
                + F("likes_count") * 3
                + F("comments_count") * 5
                + F("shares_count") * 7
                + F("saves_count") * 4
            ),
        )
        .distinct()
    )

    qs = _get_post_with_interactions(user, filtered_qs)
    post = qs.order_by(
        "has_impression", "last_impression", "-content_score", "-created_at"
    ).first()

    if post:
        Impression.objects.update_or_create(
            user=user, post=post, defaults={"viewed_at": timezone.now()}
        )
        return _serialize_post(user, post)
    return GenericResponse(detail="You have reached the end of content.")


@content_router.get("/feeds/friends/", response=PostSchema | GenericResponse, auth=auth)
def feed_friends(request: HttpRequest):
    user = cast(User, request.user)
    following_ids = Follow.objects.filter(follower=user).values_list(
        "following_id", flat=True
    )

    impression_subquery = Impression.objects.filter(
        user=user, post=OuterRef("pk")
    ).values("viewed_at")[:1]

    qs = Post.objects.filter(author_id__in=following_ids).annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
        shares_count=Count("shares", distinct=True),
        saves_count=Count("saves", distinct=True),
        last_impression=Subquery(impression_subquery),
        has_impression=Exists(
            Impression.objects.filter(user=user, post=OuterRef("pk"))
        ),
        engagement_score=(
            F("likes_count") * 3
            + F("comments_count") * 5
            + F("shares_count") * 7
            + F("saves_count") * 4
        ),
    )

    qs = _get_post_with_interactions(user, qs)
    post = qs.order_by(
        "has_impression", "last_impression", "-engagement_score", "-created_at"
    ).first()

    if post:
        Impression.objects.update_or_create(
            user=user, post=post, defaults={"viewed_at": timezone.now()}
        )
        return _serialize_post(user, post)
    return GenericResponse(detail="You have reached the end of content.")


@content_router.get("/feeds/explore/", response=PostSchema | GenericResponse, auth=auth)
def feed_explore(request: HttpRequest):
    user = cast(User, request.user)
    following_ids = set(
        Follow.objects.filter(follower=user).values_list("following_id", flat=True)
    )

    base_qs = Post.objects.exclude(author=user).exclude(author_id__in=following_ids)

    impression_subquery = Impression.objects.filter(
        user=user, post=OuterRef("pk")
    ).values("viewed_at")[:1]

    filtered_qs = base_qs.annotate(
        likes_count=Count("likes", distinct=True),
        comments_count=Count("comments", distinct=True),
        shares_count=Count("shares", distinct=True),
        saves_count=Count("saves", distinct=True),
        theme_diversity=Count("themes", distinct=True),
        last_impression=Subquery(impression_subquery),
        has_impression=Exists(
            Impression.objects.filter(user=user, post=OuterRef("pk"))
        ),
        engagement_score=(
            F("likes_count") * 3
            + F("comments_count") * 5
            + F("shares_count") * 7
            + F("saves_count") * 4
            + F("theme_diversity") * 2
        ),
    ).distinct()

    qs = _get_post_with_interactions(user, filtered_qs)
    post = qs.order_by(
        "has_impression", "last_impression", "-engagement_score", "?"
    ).first()

    if post:
        Impression.objects.update_or_create(
            user=user, post=post, defaults={"viewed_at": timezone.now()}
        )
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


@content_router.get(
    "/interactions/comments/", response=PaginatedCommentsSchema, auth=auth
)
def fetch_comments(
    request: HttpRequest,
    post_id: int,
    offset: int = 0,
    limit: int = 20,
):
    post = Post.objects.filter(id=post_id).first()
    if not post:
        return PaginatedCommentsSchema(comments=[], total=0, offset=0, limit=0)

    comments_qs = Comment.objects.filter(post=post).order_by("-created_at")
    total = comments_qs.count()
    comments = comments_qs[offset : offset + limit]

    serialized = [
        CommentSchema(
            id=c.id,
            user_id=str(c.user.id),
            username=c.user.username or "",
            text=c.text,
            created_at=c.created_at,
        )
        for c in comments.select_related("user")
    ]

    return PaginatedCommentsSchema(
        comments=serialized,
        total=total,
        offset=offset,
        limit=limit,
    )


@content_router.post("/interactions/comment/", response=CommentSchema, auth=auth)
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


@content_router.post("/interactions/share/", response=ShareResponseSchema, auth=auth)
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
    share = Share.objects.filter(slug=slug).select_related("post", "user").first()
    if not share:
        return {"error": "Invalid share link"}

    return {
        "post_id": share.post.id,
        "shared_by_user_id": share.user.id,
        "media_url": share.post.media_url,
        "caption": share.post.caption,
    }


@content_router.post("/posts/", auth=auth)
def create_post(
    request: HttpRequest,
    caption: str = Form(...),  # type:ignore
    media_url: str | None = Form(None),  # type:ignore
    themes: list[str] = Form(...),  # type:ignore
    media_file: UploadedFile | None = File(None),  # type:ignore
):
    user = request.user

    if not media_url and not media_file:
        raise ValidationError(
            [{"detail": "Either media_url or media_file must be provided"}]
        )

    with transaction.atomic():
        post_obj = Post(author=user, caption=caption)

        if media_file:
            post_obj.media_file = media_file
        elif media_url:
            post_obj.media_url = media_url

        post_obj.save()

        post_obj.themes.set(
            [Theme.objects.get_or_create(name=theme_name)[0] for theme_name in themes]
        )

    process_post_video_async(post_obj)
    return {
        "id": post_obj.id,
        "media": post_obj.media(),
        "caption": post_obj.caption,
    }


@content_router.get(
    "/posts/{post_id}/", response=PostSchema | GenericResponse, auth=auth
)
def get_post_by_id(request: HttpRequest, post_id: int):
    user = cast(User, request.user)
    post_qs = Post.objects.filter(id=post_id)
    if not post_qs.exists():
        return GenericResponse(detail="Post not found")

    qs = _get_post_with_interactions(user, post_qs)
    post = qs.first()
    if not post:
        return GenericResponse(detail="Post not found")

    Impression.objects.get_or_create(user=user, post=post)
    return _serialize_post(user, post)


@content_router.get("/posts/user/{user_id}/", response=list[PostSchema], auth=auth)
def get_post_by_user_id(request: HttpRequest, user_id: str):
    user = cast(User, request.user)
    return_posts: list[PostSchema] = []
    post_qs = Post.objects.filter(author__id=user_id).order_by("-created_at")

    if not post_qs.exists():
        return return_posts

    qs = _get_post_with_interactions(user, post_qs)
    posts = list(qs)
    if not posts:
        return return_posts

    for post in posts:
        return_posts.append(_serialize_post(user, post))

    return return_posts
