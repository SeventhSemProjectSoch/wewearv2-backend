from typing import cast

from django.http import HttpRequest
from ninja import Router

from content.models import Follow
from project.schemas import GenericResponse
from users.auth import JWTAuth
from users.models import User

follow_router = Router(tags=["Follow"])
auth = JWTAuth()


@follow_router.post("/follow/{user_id}/", response=GenericResponse, auth=auth)
def follow_user(request: HttpRequest, user_id: str):
    user = cast(User, request.user)
    target = User.objects.filter(id=user_id).first()
    if not target:
        return GenericResponse(detail="User not found")
    if target == user:
        return GenericResponse(detail="Cannot follow yourself")

    Follow.objects.get_or_create(follower=user, following=target)
    return GenericResponse(detail=f"You are now following {target.id}")


@follow_router.delete("/follow/{user_id}/", response=GenericResponse, auth=auth)
def unfollow_user(request: HttpRequest, user_id: str):
    user = cast(User, request.user)
    target = User.objects.filter(id=user_id).first()
    if not target:
        return GenericResponse(detail="User not found")

    Follow.objects.filter(follower=user, following=target).delete()
    return GenericResponse(detail=f"You unfollowed {target.id}")


@follow_router.get("/followers/{user_id}/", response=list[str], auth=auth)
def list_followers(request: HttpRequest, user_id: str) -> list[str]:
    target = User.objects.filter(id=user_id).first()
    if not target:
        return []
    followers = Follow.objects.filter(following=target).values_list(
        "follower__id", flat=True
    )
    return list(map(str, followers))


@follow_router.get("/following/{user_id}/", response=list[str], auth=auth)
def list_following(request: HttpRequest, user_id: str) -> list[str]:
    target = User.objects.filter(id=user_id).first()
    if not target:
        return []
    following = Follow.objects.filter(follower=target).values_list(
        "following__id", flat=True
    )
    return list(map(str, following))
