from celery.utils.log import get_task_logger
import waffle
from django.core.mail.message import EmailMultiAlternatives
from django.utils import timezone
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import get_object_or_404


from config.celery import app
from . import models

logger = get_task_logger(__name__)


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

        django_email_message = EmailMultiAlternatives(
            subject=email_message.subject,
            from_email=email_message.sender,
            to=to,
            body=msg,
        )
        if html_msg:
            django_email_message.attach_alternative(html_msg, "text/html")
        for attachment in attachments:
            django_email_message.attach(
                attachment["filename"], attachment["content"], attachment["mimetype"]
            )
        if email_message.postmark_message_stream:
            django_email_message.message_stream = email_message.postmark_message_stream

        if waffle.switch_is_active("disable_outbound_email"):
            raise RuntimeError("disable_outbound_email waffle flag is True")
        else:
            django_email_message.send()

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
