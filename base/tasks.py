from celery.utils.log import get_task_logger
from config.celery import app

logger = get_task_logger(__name__)


@app.task
def email_message_webhook_process(webhook_id):
    """Processes a Postmark email webhook related to an outgoing email."""
    logger.info(
        f"EmailMessageWebhook.id={webhook_id} process_email_message_webhook task started"
    )
    from base.services import email_message_webhook_process
    from base.selectors import email_message_webhook_list

    webhook = email_message_webhook_list(id=webhook_id).get()
    email_message_webhook_process(email_message_webhook=webhook)


@app.task(serializer="pickle")
def email_message_send(email_message_id, attachments=[]):
    logger.info(f"EmailMessage.id={email_message_id} send_email_message task started")

    from base.services import email_message_send
    from base.selectors import email_message_list

    email_message = email_message_list(id=email_message_id).get()
    email_message_send(email_message=email_message, attachments=attachments)
