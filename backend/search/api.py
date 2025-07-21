from django.db.models import Count
from django.db.models import Q
from django.http import HttpRequest
from ninja import Router

from content.models import Post
from content.models import Theme
from content.schemas import PostSchema
from users.models import User
from users.schemas import ThemeModelSchema

from .schemas import PostOut
from .schemas import ThemeOut
from .schemas import UserOut

search_router = Router(tags=["Search"])


def extract_hashtags(caption: str | None) -> list[str]:
    if not caption:
        return []
    import re

    return re.findall(r"#(\w+)", caption.lower())


@search_router.get("/users/", response=list[UserOut])
def search_users(
    request: HttpRequest,
    q: str,
    limit: int = 20,
    offset: int = 0,
):
    qs = User.objects.filter(
        Q(username__icontains=q)
        | Q(full_name__icontains=q)
        | Q(bio__icontains=q)
    ).order_by("username")[offset : offset + limit]
    return [
        UserOut(
            id=str(user.id),
            username=user.username,
            full_name=user.full_name,
            bio=user.bio,
        )
        for user in qs
    ]


@search_router.get("/posts/", response=list[PostSchema])
def search_posts(
    request: HttpRequest,
    q: str,
    limit: int = 20,
    offset: int = 0,
):
    theme_matches = Theme.objects.filter(name__icontains=q).values_list(
        "id", flat=True
    )

    qs = (
        Post.objects.filter(
            Q(themes__in=theme_matches) | Q(caption__icontains=q)
        )
        .distinct()
        .order_by("-created_at")[offset : offset + limit]
    )
    # print([i.author for i in qs.all()])
    qs = qs.prefetch_related("themes", "author")

    results: list[PostOut] = []
    for post in qs:
        results.append(
            PostOut(
                id=post.id,
                author_id=str(post.author.id),
                author_username=post.author.username,
                caption=post.caption,
                themes=[theme.name for theme in post.themes.all()],
            )
        )
    return results


@search_router.get("/themes/", response=list[ThemeModelSchema])
def search_themes(
    request: HttpRequest,
    q: str,
    used_only: bool = False,
    limit: int = 20,
    offset: int = 0,
):
    qs = Theme.objects.filter(name__icontains=q)
    if used_only:
        qs = qs.annotate(post_count=Count("posts")).filter(post_count__gt=0)
    return qs.order_by("name")[offset : offset + limit]
