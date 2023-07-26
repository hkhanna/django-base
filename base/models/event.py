import uuid
from django.db import models


class Event(models.Model):
    """A discrete event that occurs with respect to one or more other models in the system."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    occurred_at = models.DateTimeField()
    type = models.CharField(max_length=127)
    data = models.JSONField(
        default=dict,
        blank=True,
    )
