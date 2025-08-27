from django.contrib import admin
from django.utils.html import format_html

from project.forms import ComponentBaseForm
from project.forms import DataListFormComponent
from project.forms import ImageUploadFormComponent

from .models import BodyType
from .models import Theme
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin[User]):
    form = ComponentBaseForm
    form.components = [
        DataListFormComponent([(BodyType, "body_type")]),
        ImageUploadFormComponent(["profile_picture"]),
    ]
    readonly_fields = ("profile_picture_render",)
    fieldsets = (
        (
            "BaseInfo",
            {
                "fields": (
                    "email",
                    "gender",
                    "phone",
                    "username",
                    "full_name",
                    "bio",
                ),
            },
        ),
        (
            "Pictures",
            {
                "fields": (
                    "profile_picture_render",
                    "profile_picture",
                )
            },
        ),
        (
            "Content Prefrences",
            {
                "fields": ("height", "weight", "body_type", "themes"),
                "description": "These fields are responsible for content suggestions",
            },
        ),
    )
    list_filter = ("gender", "body_type", "themes")
    list_display = ("email", "profile_picture_render")

    @admin.display(description="Profile Picture Preview")
    def profile_picture_render(self, obj: User) -> str:
        print("here")
        url = obj.profile_picture
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


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin[Theme]):
    list_display = ("name",)


@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin[BodyType]):
    list_display = ("name",)
