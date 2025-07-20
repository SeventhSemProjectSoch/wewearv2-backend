from __future__ import annotations

from django.contrib import admin

from .models import Theme
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin[User]):
    pass


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin[Theme]):
    pass
