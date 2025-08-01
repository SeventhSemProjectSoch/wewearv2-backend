from django.contrib import admin

from project.forms import DataListForm

from .models import BodyType
from .models import Theme
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = DataListForm
    form.model_field_tuple = [(BodyType, "body_type")]
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
        ("Pictures", {"fields": ("profile_picture",)}),
        (
            "Content Prefrences",
            {
                "fields": ("height", "weight", "body_type", "themes"),
                "description": "These fields are responsible for content suggestions",
            },
        ),
    )
    list_filter = ("gender", "body_type", "themes")


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin[Theme]):
    list_display = ("name",)


@admin.register(BodyType)
class BodyTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
