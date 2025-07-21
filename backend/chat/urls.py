from django.urls import URLResolver
from django.urls import re_path

from .chatting import ChatConsumer

websocket_urlpatterns: list[URLResolver] = [
    re_path(
        r"ws/chat/(?P<user_id>\d+)/$", ChatConsumer.as_asgi()  # type:ignore
    ),
]
