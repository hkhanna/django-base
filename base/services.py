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
from typing import List
from datetime import datetime
from typing import Optional
from django.utils import timezone
from django.conf import settings
from django.template.loader import render_to_string
from datetime import timedelta
from django.utils import timezone
from importlib import import_module
from .models import EmailMessage
from .models.event import Event
from . import tasks

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


class EmailMessageService:
    def __init__(self, **kwargs: dict) -> None:
        self.email_message = EmailMessage.objects.create(**kwargs)

    def _trim_string(self, field: str) -> str:
        """Remove superfluous linebreaks and whitespace"""
        lines = field.splitlines()
        sanitized_lines = []
        for line in lines:
            sanitized_line = line.strip()
            if sanitized_line:  # Remove blank lines
                sanitized_lines.append(line.strip())
        sanitized = " ".join(sanitized_lines).strip()
        return sanitized

    def _prepare(self) -> None:
        """Updates the context with defaults and other sanity checking"""
        e = self.email_message

        assert settings.SITE_CONFIG["default_from_email"] is not None
        e.sender_email = self._trim_string(
            e.sender_email or settings.SITE_CONFIG["default_from_email"]
        )
        e.sender_name = self._trim_string(
            e.sender_name or settings.SITE_CONFIG["default_from_name"] or ""
        )
        e.reply_to_email = self._trim_string(e.reply_to_email or "")
        e.reply_to_name = self._trim_string(e.reply_to_name or "")
        e.to_name = self._trim_string(e.to_name)
        e.to_email = self._trim_string(e.to_email)

        if e.reply_to_name and not e.reply_to_email:
            e.status = EmailMessage.Status.ERROR
            e.save()
            raise RuntimeError("Reply to has a name but does not have an email")

        if not e.postmark_message_stream:
            e.postmark_message_stream = settings.POSTMARK_DEFAULT_STREAM_ID

        default_context = {
            "logo_url": settings.SITE_CONFIG["logo_url"],
            "logo_url_link": settings.SITE_CONFIG["logo_url_link"],
            "contact_email": settings.SITE_CONFIG["contact_email"],
            "site_name": settings.SITE_CONFIG["name"],
            "company": settings.SITE_CONFIG["company"],
            "company_address": settings.SITE_CONFIG["company_address"],
            "company_city_state_zip": settings.SITE_CONFIG["company_city_state_zip"],
        }
        for k, v in default_context.items():
            if k not in e.template_context:
                e.template_context[k] = v

        # Render subject from template if not already set
        if not e.subject:
            e.subject = render_to_string(
                "{0}_subject.txt".format(e.template_prefix), e.template_context
            )
        e.subject = self._trim_string(e.subject)
        if len(e.subject) > settings.MAX_SUBJECT_LENGTH:
            e.subject = e.subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
        e.template_context["subject"] = e.subject

        e.status = EmailMessage.Status.READY
        e.save()

    def _cooling_down(self, period: int, allowed: int, scopes: List[str]) -> bool:
        """Check that this created_by/template_prefix/to_email combination hasn't been recently sent.
        You can tighten the suppression by removing scopes. An empty list will cancel if any email
        at all has been sent in the cooldown period."""
        e = self.email_message
        cooldown_period = timedelta(seconds=period)
        email_messages = EmailMessage.objects.filter(
            sent_at__gt=timezone.now() - cooldown_period
        )
        if "created_by" in scopes:
            email_messages = email_messages.filter(created_by=e.created_by)
        if "template_prefix" in scopes:
            email_messages = email_messages.filter(template_prefix=e.template_prefix)
        if "to" in scopes:
            email_messages = email_messages.filter(to_email=e.to_email)

        return email_messages.count() >= allowed

    def send_email(
        self,
        attachments=[],
        cooldown_period=180,
        cooldown_allowed=1,
        scopes: List[str] = ["created_by", "template_prefix", "to"],
    ) -> bool:
        e = self.email_message
        if e.status != EmailMessage.Status.NEW:
            raise RuntimeError(
                f"EmailMessage.id={e.id} EmailMessage.send() called on an email that is not status=NEW"
            )
        self._prepare()

        if self._cooling_down(cooldown_period, cooldown_allowed, scopes):
            e.status = EmailMessage.Status.CANCELED
            e.error_message = "Cooling down"
            e.save()
            return False
        else:
            tasks.send_email_message.delay(e.id, attachments)
            return True
