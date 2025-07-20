from django.conf import settings
from django.conf.urls.static import static  # type:ignore
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from chat.api import chat_router
from content.api import content_router
from notifications.api import notifications_router
from search.api import search_router
from users.api import profile_router
from users.api import users_router

api = NinjaAPI()
api.add_router("/auth", users_router)
api.add_router("/profile", profile_router)
api.add_router("/content", content_router)
api.add_router("/search", search_router)
api.add_router("/notifications", notifications_router)
api.add_router("/chat", chat_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
