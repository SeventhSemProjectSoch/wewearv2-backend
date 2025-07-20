from ninja import Router

from users.auth import create_access_token
from users.models import OTP
from users.models import User
from users.schemas import RequestOTPSchema
from users.schemas import TokenSchema
from users.schemas import VerifyOTPSchema

router = Router(tags=["Authentication"])


def send_otp(identifier: str, code: str):
    print(f"Sending OTP {code} to {identifier}")


@router.post("/request-otp")
def request_otp(payload: RequestOTPSchema):
    identifier = payload.email or payload.phone
    if not identifier:
        return {"error": "Email or phone is required"}

    code = OTP.generate_code()
    OTP.objects.create(identifier=identifier, code=code)
    send_otp(identifier, code)
    return {"message": "OTP sent"}


@router.post("/verify-otp", response=TokenSchema)
def verify_otp(payload: VerifyOTPSchema):
    identifier = payload.email or payload.phone
    if not identifier:
        return {"error": "Email or phone is required"}

    try:
        otp = OTP.objects.filter(
            identifier=identifier, code=payload.code
        ).latest("created_at")
    except OTP.DoesNotExist:
        return {"error": "Invalid OTP"}

    if otp.is_expired():
        return {"error": "OTP expired"}

    user, _ = User.objects.get_or_create(
        email=payload.email if payload.email else None,
        phone=payload.phone if payload.phone else None,
    )

    token = create_access_token(sub=str(user.id))
    return {"access_token": token}
