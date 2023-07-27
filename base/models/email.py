import logging
from django.db import models
from django.conf import settings

from base import constants
from .. import tasks
from base.models.event import BaseModel

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """Keep a record of every email sent in the DB."""

    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        help_text="User that caused the EmailMessage to be created.",
        null=True,
    )
    org = models.ForeignKey(
        "base.Org",
        on_delete=models.SET_NULL,
        help_text="The active Org of the User that caused the EmailMessage to be created.",
        null=True,
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

    def __str__(self):
        # This will return something like 'reset-password' since its the last part of the template prefix
        template_prefix = self.template_prefix.split("/")[-1]
        return f"{template_prefix} - {self.to_email}"


class EmailMessageWebhook(BaseModel):
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
