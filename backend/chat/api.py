from typing import cast

from django.db.models import Max
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from content.models import Follow
from project.schemas import GenericResponse
from users.auth import JWTAuth
from users.models import User

from .models import Message
from .schemas import ConversationOut
from .schemas import MessageIn
from .schemas import MessageModelSchema

auth = JWTAuth()
chat_router = Router(tags=["Chat"])


def are_mutual_followers(user1: User, user2: User) -> bool:
    return (
        Follow.objects.filter(follower=user1, following=user2).exists()
        and Follow.objects.filter(follower=user2, following=user1).exists()
    )


@chat_router.post(
    "/send/",
    response={
        200: MessageModelSchema,
        403: GenericResponse,
    },
    auth=auth,
)
def send_message(request: HttpRequest, payload: MessageIn):
    sender = cast(User, request.user)
    receiver = get_object_or_404(User, id=payload.receiver_id)

    if sender != receiver and not are_mutual_followers(sender, receiver):
        return 403, GenericResponse(error="Users are not mutual followers.")

    return Message.objects.create(
        sender=sender,
        receiver=receiver,
        content=payload.content,
    )


@chat_router.get("/history/", response=list[MessageModelSchema], auth=auth)
def conversation_history(
    request: HttpRequest,
    with_user_id: str,
    limit: int = 20,
    offset: int = 0,
):
    user = cast(User, request.user)
    other_user = get_object_or_404(User, id=with_user_id)

    qs = Message.objects.filter(
        Q(sender=user, receiver=other_user)
        | Q(sender=other_user, receiver=user)
    ).order_by("-created_at")[offset : offset + limit]
    return qs


@chat_router.get("/conversations/", response=list[ConversationOut], auth=auth)
def list_conversations(
    request: HttpRequest,
    limit: int = 20,
    offset: int = 0,
):
    user = cast(User, request.user)
    qs = (
        Message.objects.filter(Q(sender=user) | Q(receiver=user))
        .values("sender", "receiver")
        .annotate(last_timestamp=Max("created_at"))
        .order_by("-last_timestamp")
    )

    seen: set[str] = set()
    conversations: list[ConversationOut] = []
    for row in qs:
        other_id = (
            row["receiver"] if row["sender"] == user.id else row["sender"]
        )
        if other_id in seen:
            continue
        seen.add(other_id)
        other_user = User.objects.get(id=other_id)
        last_msg = (
            Message.objects.filter(
                Q(sender=user, receiver=other_user)
                | Q(sender=other_user, receiver=user)
            )
            .order_by("-created_at")
            .first()
        )
        if last_msg:
            conversations.append(
                ConversationOut(
                    user_id=str(other_user.id),
                    username=other_user.username or str(other_id),
                    last_message=last_msg.content,
                    last_timestamp=last_msg.created_at,
                    profile_url=other_user.profile_picture,
                )
            )

    return conversations[offset : offset + limit]
