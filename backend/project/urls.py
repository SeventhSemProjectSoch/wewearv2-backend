from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from users.api import profile_router
from users.api import users_router

api = NinjaAPI()
api.add_router("/auth/", users_router)
api.add_router("/profile/", profile_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]
