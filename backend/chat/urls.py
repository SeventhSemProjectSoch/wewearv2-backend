from typing import Any
from typing import cast

from django.urls import URLPattern
from django.urls import URLResolver
from django.urls import re_path

from .chatting import ChatConsumer

websocket_urlpatterns: Any = [  # type:ignore
    re_path(
        r"ws/chat/(?P<user_id>\d+)/$", ChatConsumer.as_asgi()  # type:ignore
    )
]
websocket_urlpatterns = cast(
    list[URLResolver | URLPattern], websocket_urlpatterns
)
