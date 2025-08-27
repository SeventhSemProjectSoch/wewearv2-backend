from typing import List
from typing import cast

from django.urls import URLPattern
from django.urls import re_path

from .chatting import ChatConsumer

# Channels websocket URL patterns
# Pyright can't infer types for ASGI apps, so we ignore it
websocket_urlpatterns = [  # type:ignore
    re_path(r"ws/chat/(?P<user_id>\d+)/$", ChatConsumer.as_asgi())  # type: ignore[arg-type]
]
websocket_urlpatterns = cast(List[URLPattern], websocket_urlpatterns)
