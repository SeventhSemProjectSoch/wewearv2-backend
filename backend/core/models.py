from datetime import datetime

from django.db import models


class BaseModel(models.Model):
    id: models.BigAutoField[int, int] = models.BigAutoField(primary_key=True)
    created_at: models.DateTimeField[
        datetime, datetime
    ] = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
