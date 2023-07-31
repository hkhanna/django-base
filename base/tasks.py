from celery.utils.log import get_task_logger
import traceback
from datetime import datetime as dt
from django.shortcuts import get_object_or_404
from base import constants


from config.celery import app
from . import models

logger = get_task_logger(__name__)


@app.task
def process_email_message_webhook(webhook_id):
    """Processes a Postmark email webhook related to an outgoing email."""
    logger.info(
        f"EmailMessageWebhook.id={webhook_id} process_email_message_webhook task started"
    )

    try:
        webhook = get_object_or_404(models.EmailMessageWebhook, id=webhook_id)
        if webhook.status != constants.EmailMessageWebhook.Status.NEW:
            raise RuntimeError(
                f"EmailMessageWebhook.id={webhook_id} process_email_message_webhook called on a webhook that is not status=NEW"
            )
        webhook.status = constants.EmailMessageWebhook.Status.PENDING
        webhook.save()

        # Store the type
        if "RecordType" in webhook.body:
            webhook.type = webhook.body["RecordType"]

        # Find the related EmailMessage and connect it
        if "MessageID" in webhook.body:
            email_message = models.EmailMessage.objects.filter(
                message_id=webhook.body["MessageID"]
            ).first()
            if email_message:
                webhook.email_message = email_message
                if webhook.type in constants.WEBHOOK_TYPE_TO_EMAIL_STATUS:
                    # Make sure this is the most recent webhook, in case it arrived out of order.
                    all_ts = []
                    for other_webhook in models.EmailMessageWebhook.objects.filter(
                        email_message=email_message
                    ):
                        ts_key = constants.WEBHOOK_TYPE_TO_TIMESTAMP[other_webhook.type]
                        ts = other_webhook.body[ts_key]
                        ts = ts.replace("Z", "+00:00")
                        all_ts.append(dt.fromisoformat(ts))
                    all_ts.sort()

                    ts_key = constants.WEBHOOK_TYPE_TO_TIMESTAMP[webhook.type]
                    ts = webhook.body[ts_key]
                    ts = ts.replace("Z", "+00:00")
                    ts_dt = dt.fromisoformat(ts)
                    if len(all_ts) == 0 or all_ts[-1] < ts_dt:
                        new_status = constants.WEBHOOK_TYPE_TO_EMAIL_STATUS[
                            webhook.type
                        ]
                        email_message.status = new_status
                        email_message.status_updated_at = ts_dt
                        email_message.save()

        webhook.status = constants.EmailMessageWebhook.Status.PROCESSED
    except Exception as e:
        logger.exception(f"EmailMessageWebhook.id={webhook_id} in error state")
        webhook.status = constants.EmailMessageWebhook.Status.ERROR
        webhook.note = traceback.format_exc()
    finally:
        webhook.save()
        logger.debug(f"Saved EmailMessageWebhook.id={webhook_id}")


@app.task(serializer="pickle")
def email_message_send(email_message_id, attachments=[]):
    logger.info(f"EmailMessage.id={email_message_id} send_email_message task started")

    from base.services import email_message_send
    from base.selectors import email_message_list

    email_message = email_message_list(id=email_message_id).get()
    email_message_send(email_message=email_message, attachments=attachments)
