import json
from typing import Any
from typing import cast
from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from content.models import Follow
from users.models import User

from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    user: User
    other_user_id: UUID
    room_name: str
    scope: Any

    async def connect(self) -> None:
        self.user: User = self.scope["user"]
        self.other_user_id: UUID = cast(
            UUID, self.scope["url_route"]["kwargs"]["user_id"]
        )
        self.room_name: str = (
            f"chat_{min(self.user.id, self.other_user_id)}_"
            f"{max(self.user.id, self.other_user_id)}"
        )

        if not await self.are_mutual_followers(
            self.user.id, self.other_user_id
        ):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code: int) -> None:
        await self.channel_layer.group_discard(
            self.room_name, self.channel_name
        )

    async def receive(
        self,
        text_data: str | None = None,
        bytes_data: bytes | None = None,
    ) -> None:
        _data: str = ""
        if text_data:
            _data = text_data
        elif bytes_data:
            try:
                _data = bytes_data.decode()
            except:
                pass
        data: dict[str, Any] = json.loads(_data)
        content: str = data.get("content", "")[:1500]

        message: Message = await self.create_message(
            self.user.id, self.other_user_id, content
        )

        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "sender_id": message.sender.id,
                    "receiver_id": message.receiver.id,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "read": message.read,
                },
            },
        )

    async def chat_message(self, event: dict[str, Any]) -> None:
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def create_message(
        self, sender_id: UUID, receiver_id: UUID, content: str
    ) -> Message:
        sender: User = User.objects.get(id=sender_id)
        receiver: User = User.objects.get(id=receiver_id)
        return Message.objects.create(
            sender=sender, receiver=receiver, content=content
        )

    @database_sync_to_async
    def are_mutual_followers(self, user1_id: UUID, user2_id: UUID) -> bool:
        return (
            Follow.objects.filter(
                follower_id=user1_id, following_id=user2_id
            ).exists()
            and Follow.objects.filter(
                follower_id=user2_id, following_id=user1_id
            ).exists()
        )
