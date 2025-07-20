from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin[Notification]):
    list_display = (
        "id",
        "recipient",
        "actor",
        "type",
        "post",
        "read",
        "created_at",
    )
    list_filter = ("type", "read", "created_at")
    search_fields = ("recipient__username", "actor__username", "post__id")
    readonly_fields = ("created_at",)
