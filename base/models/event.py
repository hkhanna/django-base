import logging
import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from importlib import import_module

logger = logging.getLogger(__name__)


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

    @classmethod
    def emit(cls, type, data, occurred_at=None):
        if not occurred_at:
            occurred_at = timezone.now()
        event = cls.objects.create(type=type, data=data, occurred_at=occurred_at)

        logger.info(f"Event.id={event.id} Event.type={event.type} emitted.")

        handler_str = settings.EVENT_HANDLERS.get(
            type, settings.EVENT_HANDLERS["default"]
        )
        path_parts = handler_str.split(".")
        module_path = ".".join(path_parts[:-1])
        module = import_module(module_path)
        handler = getattr(module, path_parts[-1])

        handler(event)
        return event


def default_handler(event):
    # You can add code here, but a more robust solution would be to set a different handler in the settings.
    pass
