from typing import cast

# from django.http import HttpRequest
from django.http.request import HttpRequest
from ninja import Router
from ninja.errors import ValidationError

from project.schemas import GenericResponse
from users.auth import JWTAuth
from users.auth import create_access_token
from users.models import OTP
from users.models import Theme
from users.models import User
from users.schemas import ProfileSchema
from users.schemas import RequestOTPSchema
from users.schemas import TokenSchema
from users.schemas import UpdateProfileSchema
from users.schemas import VerifyOTPSchema

auth = JWTAuth()
users_router = Router(tags=["Authentication"])
profile_router = Router(tags=["Profile"])


def send_otp(identifier: str, code: str):
    print(f"Sending OTP {code} to {identifier}")


@users_router.post(
    "/request-otp",
    response={
        200: GenericResponse,
        404: GenericResponse,
    },
)
def request_otp(request: HttpRequest, payload: RequestOTPSchema):
    identifier = payload.email or payload.phone
    if not identifier:
        return 404, GenericResponse(error="Email or phone is required")

    code = OTP.generate_code()
    OTP.objects.create(identifier=identifier, code=code)
    send_otp(identifier, code)
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
    identifier = payload.email or payload.phone
    if not identifier:
        return 404, GenericResponse(**{"error": "Email or phone is required"})

    try:
        otp = OTP.objects.filter(
            identifier=identifier, code=payload.code
        ).latest("created_at")
    except OTP.DoesNotExist:
        return 409, GenericResponse(
            **{"error": f"invalid OTP for '{identifier}'."}
        )

    if otp.is_expired():
        return 410, GenericResponse(**{"error": "OTP expired"})

    user, _ = User.objects.get_or_create(
        email=payload.email if payload.email else None,
        phone=payload.phone if payload.phone else None,
    )

    token = create_access_token(sub=str(user.id))
    return 200, TokenSchema(**{"access_token": token})


@profile_router.get("/profile", response=ProfileSchema, auth=auth)
def get_profile(request: HttpRequest):
    user: User = cast(User, request.user)
    return ProfileSchema(
        username=user.username,
        full_name=user.full_name,
        bio=user.bio,
        profile_picture=user.profile_picture,
        body_type=user.body_type,
        height=user.height,
        weight=user.weight,
        themes=[t.name for t in user.themes.all()],
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

    for attr, value in _payload.items():
        setattr(user, attr, value)
    user.save()
    return get_profile(request)
