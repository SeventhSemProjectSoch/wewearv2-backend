from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.pagination import LimitOffsetPagination
from ninja.pagination import paginate  # type:ignore

from .models import Notification
from .schemas import NotificationMarkIn
from .schemas import NotificationModelSchema

notifications_router = Router(tags=["Notifications"])


@notifications_router.get(
    "/notifications/", response=list[NotificationModelSchema]
)
@paginate(LimitOffsetPagination)  # type:ignore
def list_notifications(
    request: HttpRequest,
    read: bool | None = None,
):
    qs = Notification.objects.filter(recipient=request.user)
    if read is not None:
        qs = qs.filter(read=read)
    return qs


@notifications_router.post(
    "/notifications/{notification_id}/mark/", response=NotificationModelSchema
)
def mark_notification(
    request: HttpRequest, notification_id: int, payload: NotificationMarkIn
):
    notification = get_object_or_404(
        Notification, id=notification_id, recipient=request.user
    )
    notification.read = payload.read
    notification.save()
    return notification
