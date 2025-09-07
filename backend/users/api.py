from threading import Thread
from typing import cast

from django.core.mail import send_mail
from django.http import HttpRequest
from ninja import Router

from content.models import Follow, Post
from project.env import ENV
from project.schemas import GenericResponse
from users.auth import JWTAuth, create_access_token
from users.models import OTP, BodyType, Theme, User
from users.schemas import (
    ProfileSchema,
    RequestOTPSchema,
    TokenSchema,
    UpdateProfileSchema,
    VerifyOTPSchema,
)

auth = JWTAuth()
users_router = Router(tags=["Authentication"])
profile_router = Router(tags=["Profile"])
meta_router = Router(tags=["Meta"])


def send_otp(identifier: str, code: str):
    send_mail(
        "Your One-Time Password (OTP)",
        f"""
Hello,

Your One-Time Password (OTP) for verification is:

{code}

Please use this OTP to complete your action. This OTP is valid for a short period.
Do not share this OTP with anyone.

If you did not request this OTP, please ignore this email.

Thank you,
[Your Application/Service Name]
    """,
        ENV.SMTP_EMAIL,
        [identifier],
        fail_silently=False,
    )
    print(f"Sending OTP {code} to {identifier}")


@users_router.post(
    "/request-otp",
    response={
        200: GenericResponse,
        404: GenericResponse,
    },
)
def request_otp(request: HttpRequest, payload: RequestOTPSchema):
    identifier = payload.email
    if not identifier:
        return 404, GenericResponse(error="Email  is required")

    code = OTP.generate_code()
    OTP.objects.create(identifier=identifier, code=code)
    Thread(
        target=send_otp,
        args=(identifier, code),
        daemon=False,
        name="Otp thread",
    ).start()
    return 200, GenericResponse(detail=f"OTP was sent to  '{identifier}'.")


@users_router.post(
    "/verify-otp",
    response={
        200: TokenSchema,
        404: GenericResponse,
        409: GenericResponse,
    },
)
def verify_otp(request: HttpRequest, payload: VerifyOTPSchema):
    identifier = payload.email
    if not identifier:
        return 404, GenericResponse(**{"error": "Email or phone is required"})

    try:
        otp = OTP.objects.filter(identifier=identifier, code=payload.code).latest(
            "created_at"
        )
    except OTP.DoesNotExist:
        return 409, GenericResponse(**{"error": f"invalid OTP for '{identifier}'."})

    if otp.is_expired():
        return 410, GenericResponse(**{"error": "OTP expired"})

    user, _ = User.objects.get_or_create(
        email=payload.email if payload.email else None,
    )

    token = create_access_token(sub=str(user.id))
    return 200, TokenSchema(**{"access_token": token})


@profile_router.get("/profile", response=ProfileSchema, auth=auth)
def get_profile(request: HttpRequest):
    user: User = cast(User, request.user)

    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    posts_count = Post.objects.filter(author=user).count()

    return ProfileSchema(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        profile_picture=user.profile_picture,
        body_type=user.body_type,
        height=user.height,
        weight=user.weight,
        themes=[t.name for t in user.themes.all()],
        followers_count=followers_count,
        following_count=following_count,
        posts_count=posts_count,
    )


@profile_router.put("/profile", response=ProfileSchema, auth=auth)
def update_profile(request: HttpRequest, payload: UpdateProfileSchema):
    _payload = payload.dict(
        exclude_unset=True,
        exclude_defaults=True,
    )

    user: User = cast(User, request.user)

    theme_objs: list[Theme] = []
    if "themes" in _payload:
        for theme_name in payload.themes:
            theme_objs.append(Theme.objects.get_or_create(name=theme_name)[0])
            user.themes.set(theme_objs)
        _payload.pop("themes")

    if "body_type" in _payload and payload.body_type:
        BodyType.objects.get_or_create(name=payload.body_type)

    for attr, value in _payload.items():
        setattr(user, attr, value)
        user.save()
    return get_profile(request)


@profile_router.get(
    "/profile/{user_id}/", response=ProfileSchema | GenericResponse, auth=auth
)
def get_user_by_id(request: HttpRequest, user_id: int):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return GenericResponse(detail="User not found")

    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    posts_count = Post.objects.filter(author=user).count()

    return ProfileSchema(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        profile_picture=user.profile_picture,
        body_type=user.body_type,
        height=user.height,
        weight=user.weight,
        themes=[t.name for t in user.themes.all()],
        followers_count=followers_count,
        following_count=following_count,
        posts_count=posts_count,
    )


@meta_router.get("/bodytypes/", response=list[str])
def list_bodytypes(request: HttpRequest):
    bodytypes = BodyType.objects.values_list("name", flat=True)
    return list(bodytypes)


@meta_router.get("/themes/", response=list[str])
def list_themes(request: HttpRequest):
    themes = Theme.objects.values_list("name", flat=True)
    return list(themes)
