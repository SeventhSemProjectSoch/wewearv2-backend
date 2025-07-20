from datetime import datetime
from datetime import timedelta
from datetime import timezone

import jwt
from django.http import HttpRequest
from ninja.security import HttpBearer

from project.env import ENV
from users.models import User

SECRET_KEY = ENV.SECRET_KEY.encode()


def create_access_token(*, sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=ENV.ACCESS_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"exp": expire, "sub": sub}
    encoded_jwt = jwt.encode(  # type:ignore
        to_encode, SECRET_KEY, algorithm=ENV.ALGORITHM
    )
    return encoded_jwt


class JWTAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str):
        try:
            payload = jwt.decode(  # type:ignore
                token, SECRET_KEY, algorithms=[ENV.ALGORITHM]
            )
            user_id = payload.get("sub")
            user = User.objects.get(id=user_id)
            return user
        except Exception:
            return None
