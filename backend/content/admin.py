from django.contrib import admin
from django.db.models import Model
from django.utils.html import format_html

from .models import Comment
from .models import Follow
from .models import Impression
from .models import Like
from .models import Post
from .models import Save
from .models import Share


@admin.register(Post)
class PostAdmin(admin.ModelAdmin[Post]):
    list_display = (
        "id",
        "author",
        "caption_short",
        "media_preview",
        "created_at",
    )
    list_filter = ("created_at", "themes")
    search_fields = ("author__username", "caption")
    readonly_fields = ("created_at", "media_preview")
    filter_horizontal = ("themes",)

    @admin.display(description="Caption")
    def caption_short(self, obj: Post) -> str:
        return (obj.caption or "")[:40]

    @admin.display(description="Media Preview")
    def media_preview(self, obj: Post) -> str:
        url = obj.media()
        if not url:
            return "-"
        if url.lower().endswith((".mp4", ".mov", ".avi")):
            return format_html(
                '<video width="150" height="100" controls muted><source src="{}" type="video/mp4"></video>',
                url,
            )
        else:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                url,
            )


class LikeInline(admin.TabularInline[Like, Model]):
    model = Like
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False
    show_change_link = True


class SaveInline(admin.TabularInline[Save, Model]):
    model = Save
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False
    show_change_link = True


class CommentInline(admin.TabularInline[Comment, Model]):
    model = Comment
    extra = 0
    readonly_fields = ("user", "created_at")
    fields = ("user", "text", "created_at")
    show_change_link = True


class ShareInline(admin.TabularInline[Share, Model]):
    model = Share
    extra = 0
    readonly_fields = ("user", "slug", "created_at")
    fields = ("user", "slug", "created_at")
    show_change_link = True


class ImpressionInline(admin.TabularInline[Impression, Model]):
    model = Impression
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False
    show_change_link = False


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin[Follow]):
    list_display = ("id", "follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
    readonly_fields = ("created_at",)


PostAdmin.inlines = [
    LikeInline,
    SaveInline,
    CommentInline,
    ShareInline,
    ImpressionInline,
]
