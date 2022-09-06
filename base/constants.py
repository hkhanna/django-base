from django.db import models


class EmailMessage:
    class Status(models.TextChoices):
        NEW = "new"
        READY = "ready"
        PENDING = "pending"
        SENT = "sent"
        DELIVERED = "delivered"
        OPENED = "opened"
        BOUNCED = "bounced"
        SPAM = "spam"
        CANCELED = "canceled"
        ERROR = "error"


# This is a mapping of Postmark RecordTypes -- which end up as
# EmailMessageWebhook.type to a new EmailMessage status when that
# webhook is received and processed.
WEBHOOK_TYPE_TO_EMAIL_STATUS = {
    "Delivery": EmailMessage.Status.DELIVERED,
    "Open": EmailMessage.Status.OPENED,
    "Bounce": EmailMessage.Status.BOUNCED,
    "SpamComplaint": EmailMessage.Status.SPAM,
}
