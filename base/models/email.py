import logging
from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings

from base import constants

from .. import tasks

logger = logging.getLogger(__name__)


class EmailMessage(models.Model):
    """Keep a record of every email sent in the DB."""

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        help_text="User that caused the EmailMessage to be created.",
    )
    sender_name = models.CharField(max_length=254, blank=True)
    sender_email = models.EmailField()
    to_name = models.CharField(max_length=254, blank=True)
    to_email = models.EmailField()
    reply_to_name = models.CharField(max_length=254, blank=True)
    reply_to_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=254, blank=True)
    template_prefix = models.CharField(max_length=254)
    template_context = models.JSONField()
    message_id = models.CharField(
        max_length=254,
        unique=True,
        null=True,
        blank=True,
        default=None,
        help_text="Message-ID provided by the sending service as per RFC 5322",
    )
    postmark_message_stream = models.CharField(
        max_length=254, blank=True, help_text="Leave blank if not using Postmark"
    )

    Status = constants.EmailMessage.Status
    status = models.CharField(
        max_length=254, choices=Status.choices, default=Status.NEW
    )
    error_message = models.TextField(blank=True)

    @staticmethod
    def _trim_string(field):
        """Remove superfluous linebreaks and whitespace"""
        lines = field.splitlines()
        sanitized_lines = []
        for line in lines:
            sanitized_line = line.strip()
            if sanitized_line:  # Remove blank lines
                sanitized_lines.append(line.strip())
        sanitized = " ".join(sanitized_lines).strip()
        return sanitized

    def cooling_down(self, period, allowed, scopes):
        """Check that this created_by/template_prefix/to_email combination hasn't been recently sent.
        You can tighten the suppression by removing scopes. An empty list will cancel if any email
        at all has been sent in the cooldown period."""
        cooldown_period = timedelta(seconds=period)
        email_messages = EmailMessage.objects.filter(
            sent_at__gt=timezone.now() - cooldown_period
        )
        if "created_by" in scopes:
            email_messages = email_messages.filter(created_by=self.created_by)
        if "template_prefix" in scopes:
            email_messages = email_messages.filter(template_prefix=self.template_prefix)
        if "to" in scopes:
            email_messages = email_messages.filter(to_email=self.to_email)

        return email_messages.count() >= allowed

    def send(
        self,
        attachments=[],
        cooldown_period=180,
        cooldown_allowed=1,
        scopes=["created_by", "template_prefix", "to"],
    ):
        if self.status != EmailMessage.Status.NEW:
            raise RuntimeError(
                f"EmailMessage.id={self.id} EmailMessage.send() called on an email that is not status=NEW"
            )
        self.prepare()

        if self.cooling_down(cooldown_period, cooldown_allowed, scopes):
            self.status = EmailMessage.Status.CANCELED
            self.error_message = "Cooling down"
            self.save()
            return False
        else:
            tasks.send_email_message.delay(self.id, attachments)
            return True

    def prepare(self):
        """Updates the context with defaults and other sanity checking"""
        self.sender_email = self._trim_string(
            self.sender_email or settings.SITE_CONFIG["default_from_email"]
        )
        self.sender_name = self._trim_string(
            self.sender_name or settings.SITE_CONFIG["default_from_name"] or ""
        )
        self.reply_to_email = self._trim_string(self.reply_to_email or "")
        self.reply_to_name = self._trim_string(self.reply_to_name or "")
        self.to_name = self._trim_string(self.to_name)
        self.to_email = self._trim_string(self.to_email)

        if self.reply_to_name and not self.reply_to_email:
            self.status = EmailMessage.Status.ERROR
            self.save()
            raise RuntimeError("Reply to has a name but does not have an email")

        if not self.postmark_message_stream:
            self.postmark_message_stream = settings.POSTMARK_DEFAULT_STREAM_ID

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
            if k not in self.template_context:
                self.template_context[k] = v

        # Render subject from template if not already set
        if not self.subject:
            self.subject = render_to_string(
                "{0}_subject.txt".format(self.template_prefix), self.template_context
            )
        self.subject = self._trim_string(self.subject)
        if len(self.subject) > settings.MAX_SUBJECT_LENGTH:
            self.subject = self.subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
        self.template_context["subject"] = self.subject

        self.status = EmailMessage.Status.READY
        self.save()

    def __str__(self):
        # This will return something like 'reset-password' since its the last part of the template prefix
        template_prefix = self.template_prefix.split("/")[-1]
        return f"{template_prefix} - {self.to_email}"


class EmailMessageWebhook(models.Model):
    """Webhooks related to an outgoing EmailMessage, like bounces, spam complaints, etc."""

    received_at = models.DateTimeField(auto_now_add=True)
    body = models.JSONField()
    headers = models.JSONField()

    type = models.CharField(max_length=254, blank=True)
    email_message = models.ForeignKey(
        EmailMessage, null=True, blank=True, on_delete=models.SET_NULL
    )
    note = models.TextField(blank=True)

    class Status(models.TextChoices):
        NEW = "new"
        PENDING = "pending"
        PROCESSED = "processed"
        ERROR = "error"

    status = models.CharField(
        max_length=127, choices=Status.choices, default=Status.NEW
    )

    def __str__(self):
        if self.type:
            return f"{self.type} ({self.id})"

    def process(self):
        tasks.process_email_message_webhook.delay(self.id)
