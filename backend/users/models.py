from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
import uuid
from secrets import token_urlsafe

from project.env import ENV


class UserManager(BaseUserManager):
    def create_user(self, email=None, phone=None):
        if not email and not phone:
            raise ValueError("Users must have an email or phone")
        user = self.model(email=email, phone=phone)
        user.set_unusable_password()
        user.save()
        return user

    def create_superuser(self, email, password=None):
        user = self.model(email=email)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return f"{self.email or self.phone}"


class OTP(models.Model):
    identifier = models.CharField(max_length=255)  # email or phone
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=5)

    @staticmethod
    def generate_code():
        return token_urlsafe(ENV.OTP_LENGTH)
