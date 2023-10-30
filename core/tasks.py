from django.conf import settings
from celery.utils.log import get_task_logger
from config.celery import app

logger = get_task_logger(__name__)


@app.task
def email_message_webhook_process(webhook_id):
    """Processes a Postmark email webhook related to an outgoing email."""
    logger.info(
        f"EmailMessageWebhook.id={webhook_id} process_email_message_webhook task started"
    )
    from core.services import email_message_webhook_process
    from core.selectors import email_message_webhook_list

    webhook = email_message_webhook_list(id=webhook_id).get()
    email_message_webhook_process(email_message_webhook=webhook)


@app.task
def email_message_send(email_message_id):
    logger.info(f"EmailMessage.id={email_message_id} send_email_message task started")

    from core.services import email_message_send
    from core.selectors import email_message_list

    email_message = email_message_list(id=email_message_id).get()
    email_message_send(email_message=email_message)


@app.task(time_limit=60 * 60)
def database_backup():
    from core.services import database_backup

    database_backup()


periodic = [
    # Backup database once per week Sunday morning at 3:16am.
    {
        "task": database_backup,
        "name": database_backup.name,
        "cron": {
            "minute": "16",
            "hour": "3",
            "day_of_week": "0",
        },
        "enabled": settings.ENABLE_DATABASE_BACKUPS,
    }
]
