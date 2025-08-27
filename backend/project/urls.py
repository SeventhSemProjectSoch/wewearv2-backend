import mimetypes
import traceback

import puremagic
from django.conf import settings
from django.conf.urls.static import static  # type:ignore
from django.contrib import admin
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.http import HttpRequest
from django.urls import path
from jwt.exceptions import ExpiredSignatureError
from jwt.exceptions import InvalidSignatureError
from ninja import NinjaAPI

from chat.api import chat_router
from content.api import content_router
from notifications.api import notifications_router
from search.api import search_router
from users.api import meta_router
from users.api import profile_router
from users.api import users_router
from users.follow_api import follow_router

api = NinjaAPI()
api.add_router("/auth", users_router)
api.add_router("/profile", profile_router)
api.add_router("/content", content_router)
api.add_router("/search", search_router)
api.add_router("/notifications", notifications_router)
api.add_router("/chat", chat_router)
api.add_router("/meta", meta_router)
api.add_router("/follow", follow_router)


@api.exception_handler(IntegrityError)
def integrity_error_handler(request: HttpRequest, exc: IntegrityError):
    return api.create_response(request, {"detail": str(exc)}, status=400)


@api.exception_handler(ObjectDoesNotExist)
def does_not_exist_handler(request: HttpRequest, exc: ObjectDoesNotExist):
    tb_str = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    print(tb_str)
    return api.create_response(request, {"detail": str(exc)}, status=400)


@api.exception_handler(InvalidSignatureError)
def not_a_valid_user(request: HttpRequest, exc: InvalidSignatureError):
    return api.create_response(request, {"detail": str(exc)}, status=400)


@api.exception_handler(ExpiredSignatureError)
def jwt_expried(request: HttpRequest, exc: ExpiredSignatureError):
    return api.create_response(request, {"detail": str(exc)}, status=401)


__Hijacked = False


def hijak_media_type_guessing():
    global __Hijacked
    if __Hijacked:
        return

    __Hijacked = True
    old_guesser = mimetypes.guess_type

    def new_guesser(url: str, strict: bool = True):
        try:
            url += puremagic.from_file(url)
        except puremagic.main.PureError:
            pass
        return old_guesser(url, strict)

    mimetypes.guess_type = new_guesser


hijak_media_type_guessing()

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("api/", api.urls),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
