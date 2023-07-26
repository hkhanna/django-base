"""
A service can be:

A simple function.
A class.
An entire module.
Whatever makes sense in your case.
In most cases, a service can be simple function that:

Lives in <your_app>/services.py module.
Takes keyword-only arguments, unless it requires no or one argument.
Is type-annotated (even if you are not using mypy at the moment).
Interacts with the database, other resources & other parts of your system.
Does business logic - from simple model creation to complex cross-cutting concerns, to calling external services & tasks.
"""

import logging
from datetime import datetime
from typing import Optional
from django.utils import timezone
from django.conf import settings
from importlib import import_module
from .models import Event

logger = logging.getLogger(__name__)


def event_emit(
    *, type: str, data: dict, occurred_at: Optional[datetime] = None
) -> Event:
    if not occurred_at:
        occurred_at = timezone.now()
    event = Event.objects.create(type=type, data=data, occurred_at=occurred_at)

    logger.info(f"Event.uuid={event.uuid} Event.type={event.type} emitted.")

    handler_str = settings.EVENT_HANDLERS.get(type, settings.EVENT_HANDLERS["default"])
    path_parts = handler_str.split(".")
    module_path = ".".join(path_parts[:-1])
    module = import_module(module_path)
    handler = getattr(module, path_parts[-1])

    handler(event)
    return event


def event_noop(event: Event) -> None:
    pass
