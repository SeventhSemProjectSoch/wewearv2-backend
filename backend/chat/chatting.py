import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from content.models import Follow
from users.models import User

from .models import Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.room_name = f"chat_{min(self.user.id, self.other_user_id)}_{max(self.user.id, self.other_user_id)}"

        if not await self.are_mutual_followers(
            self.user.id, int(self.other_user_id)
        ):
            await self.close()
            return

        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data["content"][:1500]

        message = await self.create_message(
            self.user.id, int(self.other_user_id), content
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
                    "created_at": str(message.created_at),
                    "read": message.read,
                },
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def create_message(self, sender_id, receiver_id, content):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        return Message.objects.create(
            sender=sender, receiver=receiver, content=content
        )

    @database_sync_to_async
    def are_mutual_followers(self, user1_id, user2_id):
        return (
            Follow.objects.filter(
                follower_id=user1_id, following_id=user2_id
            ).exists()
            and Follow.objects.filter(
                follower_id=user2_id, following_id=user1_id
            ).exists()
        )
