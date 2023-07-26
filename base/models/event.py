import uuid
from django.db import models


# FIXME: Temporary location until models are consolidated.
from django.utils import timezone


class BaseModel(models.Model):
    """Base model for all models"""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        help_text="Secondary ID",
    )
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Event(BaseModel):
    """A discrete event that occurs with respect to one or more other models in the system."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    occurred_at = models.DateTimeField()
    type = models.CharField(max_length=127)
    data = models.JSONField(
        default=dict,
        blank=True,
    )
