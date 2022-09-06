from celery.utils.log import get_task_logger
from django.apps import apps
import traceback
import waffle
from django.core.mail.message import EmailMultiAlternatives
from django.utils import timezone
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
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
        if webhook.status != models.EmailMessageWebhook.Status.NEW:
            raise RuntimeError(
                f"EmailMessageWebhook.id={webhook_id} process_email_message_webhook called on a webhook that is not status=NEW"
            )
        webhook.status = models.EmailMessageWebhook.Status.PENDING
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
                    new_status = constants.WEBHOOK_TYPE_TO_EMAIL_STATUS[webhook.type]
                    email_message.status = new_status
                    email_message.save()

        webhook.status = models.EmailMessageWebhook.Status.PROCESSED
    except Exception as e:
        logger.exception(f"EmailMessageWebhook.id={webhook_id} in error state")
        webhook.status = models.EmailMessageWebhook.Status.ERROR
        webhook.note = traceback.format_exc()
    finally:
        webhook.save()
        logger.debug(f"Saved EmailMessageWebhook.id={webhook_id}")


@app.task
def send_email_message(email_message_id, attachments=[]):
    logger.info(f"EmailMessage.id={email_message_id} send_email_message task started")
    email_message = get_object_or_404(models.EmailMessage, id=email_message_id)

    if email_message.status != models.EmailMessage.Status.READY:
        raise RuntimeError(
            f"EmailMessage.id={email_message_id} send_email_message called on an email that is not status=READY"
        )
    email_message.status = models.EmailMessage.Status.PENDING
    email_message.save()

    template_name = email_message.template_prefix + "_message.txt"
    html_template_name = email_message.template_prefix + "_message.html"
    try:
        msg = render_to_string(
            template_name=template_name,
            context=email_message.template_context,
        )
        html_msg = None
        try:
            html_msg = render_to_string(
                template_name=html_template_name,
                context=email_message.template_context,
            )
        except TemplateDoesNotExist:
            logger.warning(
                f"EmailMessage.id={email_message_id} template not found {html_template_name}"
            )

        if email_message.to_name:
            to = [f"{email_message.to_name} <{email_message.to_email}>"]
        else:
            to = [email_message.to_email]

        if email_message.reply_to:
            reply_to = [email_message.reply_to]
        else:
            reply_to = None

        django_email_message = EmailMultiAlternatives(
            subject=email_message.subject,
            from_email=email_message.sender,
            to=to,
            body=msg,
            reply_to=reply_to,
        )
        if html_msg:
            django_email_message.attach_alternative(html_msg, "text/html")

        for attachment in attachments:
            assert not (
                "content" in attachment
                and "content_from_instance_file_field" in attachment
            ), "Only one of 'content' or 'content_from_instance_file_field' allowed in an attachment"
            if "content" in attachment:
                content = attachment["content"]
            elif "content_from_instance_file_field" in attachment:
                spec = attachment["content_from_instance_file_field"]
                Model = apps.get_model(
                    app_label=spec["app_label"], model_name=spec["model_name"]
                )
                instance = Model.objects.get(pk=spec["pk"])
                file = getattr(instance, spec["field_name"])
                content = file.read()

            django_email_message.attach(
                attachment["filename"], content, attachment["mimetype"]
            )
        if email_message.postmark_message_stream:
            django_email_message.message_stream = email_message.postmark_message_stream

        if waffle.switch_is_active("disable_outbound_email"):
            raise RuntimeError("disable_outbound_email waffle flag is True")
        else:
            message_ids = django_email_message.send()

            # Postmark has a setting for returning MessageIDs
            if type(message_ids) is list and len(message_ids) == 1:
                email_message.message_id = message_ids[0]

    except Exception as e:
        email_message.status = models.EmailMessage.Status.ERROR
        email_message.error_message = repr(e)
        email_message.save()
        logger.exception(
            f"EmailMessage.id={email_message_id} Exception caught in send_email_message"
        )
    else:
        email_message.status = models.EmailMessage.Status.SENT
        email_message.sent_at = timezone.now()

    email_message.save()
