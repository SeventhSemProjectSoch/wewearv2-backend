import uuid
from datetime import datetime
from datetime import timedelta
from secrets import token_urlsafe

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.expressions import Combinable

from project.env import ENV


class UserManager(BaseUserManager["User"]):
    def create_user(self, email: str | None = None, phone: str | None = None):
        if not email and not phone:
            raise ValueError("Users must have an email or phone")
        user = self.model(email=email, phone=phone)
        user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, email: str, password: str | None = None):
        user = self.model(email=email)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        return user


class Theme(models.Model):
    name: models.CharField[str, str] = models.CharField(
        max_length=50, unique=True
    )

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    id: models.UUIDField[str, str] = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    email: models.CharField[str, str | None] = models.EmailField(
        unique=True, null=True, blank=True
    )
    phone: models.CharField[str, str | None] = models.CharField(
        max_length=20, unique=True, null=True, blank=True
    )
    is_active: bool | models.BooleanField[
        bool | Combinable, bool
    ] = models.BooleanField(default=True)
    is_staff: bool | models.BooleanField[
        bool | Combinable, bool
    ] = models.BooleanField(default=False)
    username: models.CharField[str, str | None] = models.CharField(
        max_length=30, unique=True, null=True, blank=True
    )
    full_name: models.CharField[str, str | None] = models.CharField(
        max_length=100, null=True, blank=True
    )
    bio: models.TextField[str, str | None] = models.TextField(
        null=True, blank=True
    )
    profile_picture: models.CharField[str, str | None] = models.URLField(
        null=True, blank=True
    )

    body_type: models.CharField[str, str | None] = models.CharField(
        max_length=50, null=True, blank=True
    )
    height: models.DecimalField[float, float | None] = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    weight: models.DecimalField[float, float | None] = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    themes: models.ManyToManyField[Theme, Theme] = models.ManyToManyField(
        Theme, blank=True, related_name="users"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email or self.phone}"


class OTP(models.Model):
    identifier: models.CharField[str, str] = models.CharField(max_length=255)
    code: models.CharField[str, str] = models.CharField(max_length=6)
    created_at: models.DateTimeField[
        datetime, datetime
    ] = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return datetime.now() > self.created_at + timedelta(minutes=5)

    @staticmethod
    def generate_code():
        return token_urlsafe(ENV.OTP_LENGTH)
