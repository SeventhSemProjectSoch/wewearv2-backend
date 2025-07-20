from typing import Annotated

from django.db.models import Max
from django.db.models import Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja import Router

from content.models import Follow
from users.models import User

from .models import Message
from .schemas import ConversationOut
from .schemas import MessageIn
from .schemas import MessageOut

chat_router = Router(tags=["Chat"])


def are_mutual_followers(user1: User, user2: User) -> bool:
    return (
        Follow.objects.filter(follower=user1, following=user2).exists()
        and Follow.objects.filter(follower=user2, following=user1).exists()
    )


@chat_router.post("/send/", response=MessageOut)
def send_message(request: HttpRequest, payload: MessageIn):
    sender = request.user
    receiver = get_object_or_404(User, id=payload.receiver_id)

    if sender != receiver and not are_mutual_followers(sender, receiver):
        return {"error": "Users are not mutual followers."}

    msg = Message.objects.create(
        sender=sender,
        receiver=receiver,
        content=payload.content,
    )
    return msg


@chat_router.get("/history/", response=list[MessageOut])
def conversation_history(
    request: HttpRequest,
    with_user_id: Annotated[int, Query()],
    limit: Annotated[int, Query(20, ge=1, le=50)] = 20,
    offset: Annotated[int, Query(0, ge=0)] = 0,
):
    user = request.user
    other_user = get_object_or_404(User, id=with_user_id)

    qs = Message.objects.filter(
        Q(sender=user, receiver=other_user)
        | Q(sender=other_user, receiver=user)
    ).order_by("-created_at")[offset : offset + limit]
    return qs


@chat_router.get("/conversations/", response=list[ConversationOut])
def list_conversations(
    request: HttpRequest,
    limit: Annotated[int, Query(20, ge=1, le=50)] = 20,
    offset: Annotated[int, Query(0, ge=0)] = 0,
):
    user = request.user
    # last message per user pair
    qs = (
        Message.objects.filter(Q(sender=user) | Q(receiver=user))
        .values("sender", "receiver")
        .annotate(last_timestamp=Max("created_at"))
        .order_by("-last_timestamp")
    )

    # get distinct users the current user has chatted with
    seen = set()
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
                    user_id=other_user.id,
                    username=other_user.username,
                    last_message=last_msg.content,
                    last_timestamp=last_msg.created_at,
                )
            )

    return conversations[offset : offset + limit]
