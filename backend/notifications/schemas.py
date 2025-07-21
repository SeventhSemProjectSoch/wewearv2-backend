from ninja import ModelSchema
from pydantic import BaseModel

from notifications.models import Notification


class NotificationMarkIn(BaseModel):
    read: bool


class NotificationModelSchema(ModelSchema):
    class Meta:
        model = Notification
        fields = "__all__"
