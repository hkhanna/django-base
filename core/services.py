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

from uuid import uuid4
import mimetypes
import logging
import traceback
from datetime import datetime, timedelta
from importlib import import_module
from typing import List, Optional, Union, Dict, Any, Type, IO, AnyStr


from django.conf import settings
from django.http import HttpRequest
from django.apps import apps
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail.message import EmailMultiAlternatives, sanitize_address
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.db.models import Model, QuerySet
from django.template import TemplateDoesNotExist

from . import selectors, tasks, utils, constants
from .tasks import email_message_send as email_message_send_task
from .exceptions import *
from .models import (
    EmailMessage,
    EmailMessageAttachment,
    EmailMessageWebhook,
    Event,
    GlobalSetting,
    Org,
    OrgInvitation,
    OrgSetting,
    OrgUserSetting,
    OrgUserSettingDefault,
    OrgUserOrgUserSetting,
    OrgUser,
    Plan,
    PlanOrgSetting,
    OverriddenOrgSetting,
)
from .types import BaseModelType, UserType

logger = logging.getLogger(__name__)


def event_emit(
    *, type: str, data: dict, occurred_at: Optional[datetime] = None
) -> Event:
    if not occurred_at:
        occurred_at = timezone.now()
    event = event_create(type=type, data=data, occurred_at=occurred_at)

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


def event_create(**kwargs) -> Event:
    return model_create(klass=Event, **kwargs)


def event_update(instance: Event, **kwargs) -> Event:
    return model_update(instance=instance, data=kwargs)


def email_message_check_cooling_down(
    *, email_message: EmailMessage, period: int, allowed: int, scopes: List[str]
) -> bool:
    """Check that this created_by/template_prefix/to_email combination hasn't been recently sent.
    You can tighten the suppression by removing scopes. An empty list will cancel if any email
    at all has been sent in the cooldown period."""
    e = email_message
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


def email_message_prepare(*, email_message: EmailMessage) -> None:
    """Updates the context with defaults and other sanity checking"""
    e = email_message

    if e.status != constants.EmailMessage.Status.NEW:
        raise RuntimeError(
            f"EmailMessage.id={e.id} email_message_prepare() called on an email that is not status=NEW"
        )

    assert settings.SITE_CONFIG["default_from_email"] is not None
    email_message_update(
        instance=e,
        sender_email=utils.trim_string(
            field=e.sender_email or settings.SITE_CONFIG["default_from_email"]
        ),
        sender_name=utils.trim_string(
            field=e.sender_name or settings.SITE_CONFIG["default_from_name"] or ""
        ),
        reply_to_email=utils.trim_string(field=e.reply_to_email or ""),
        reply_to_name=utils.trim_string(field=e.reply_to_name or ""),
        to_name=utils.trim_string(field=e.to_name),
        to_email=utils.trim_string(field=e.to_email),
    )

    if e.reply_to_name and not e.reply_to_email:
        email_message_update(instance=e, status=constants.EmailMessage.Status.ERROR)
        raise RuntimeError("Reply to has a name but does not have an email")

    if not e.postmark_message_stream:
        email_message_update(
            instance=e, postmark_message_stream=settings.POSTMARK_DEFAULT_STREAM_ID
        )

    # Set defaults for template context if not provided.
    template_context = {
        "logo_url": settings.SITE_CONFIG["logo_url"],
        "logo_url_link": settings.SITE_CONFIG["logo_url_link"],
        "contact_email": settings.SITE_CONFIG["contact_email"],
        "site_name": settings.SITE_CONFIG["name"],
        "company": settings.SITE_CONFIG["company"],
        "company_address": settings.SITE_CONFIG["company_address"],
        "company_city_state_zip": settings.SITE_CONFIG["company_city_state_zip"],
    } | e.template_context

    # Render subject from template if not already set
    subject = e.subject
    if not subject:
        subject = render_to_string(
            "{0}_subject.txt".format(e.template_prefix), template_context
        )
    subject = utils.trim_string(field=subject)
    if len(subject) > settings.MAX_SUBJECT_LENGTH:
        subject = subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
    template_context["subject"] = subject

    email_message_update(
        instance=e,
        template_context=template_context,
        subject=subject,
        status=constants.EmailMessage.Status.READY,
    )


def email_message_attach(
    *,
    email_message: EmailMessage,
    file: IO[AnyStr] | AnyStr,
    filename: str,
    mimetype: str,
) -> EmailMessageAttachment:
    """Attach a file to an EmailMessage via EmailMessageAttachment.
    For convenience, file can be a python file object or string or bytes of content.
    """

    if email_message.status != constants.EmailMessage.Status.READY:
        raise RuntimeError(
            f"EmailMessage.id={email_message.id} email_message_attach called on an email that is not status=READY. Did you run email_message_prepare()?"
        )

    # Filename's extension must match mimetype
    expected = mimetypes.guess_type(filename)[0]
    if mimetype != expected:
        raise ApplicationError(
            f"Filename {filename} does not match mimetype {mimetype}"
        )

    ext = mimetypes.guess_extension(mimetype)  # For storage on S3
    uuid = uuid4()

    if not isinstance(file, (str, bytes)):
        django_file = File(file, name=f"{uuid}{ext}")
    else:
        django_file = ContentFile(file, name=f"{uuid}{ext}")

    attachment = email_message_attachment_create(
        uuid=uuid,
        email_message=email_message,
        filename=filename,
        mimetype=mimetype,
        file=django_file,
    )
    return attachment


def email_message_queue(
    *,
    email_message: EmailMessage,
    cooldown_period=180,
    cooldown_allowed=1,
    scopes: List[str] = ["created_by", "template_prefix", "to"],
) -> bool:
    e = email_message

    # If we've pre-prepared the email, skip the prepare step.
    if e.status != constants.EmailMessage.Status.READY:
        email_message_prepare(email_message=e)

    if email_message_check_cooling_down(
        email_message=e,
        period=cooldown_period,
        allowed=cooldown_allowed,
        scopes=scopes,
    ):
        email_message_update(
            instance=e,
            status=constants.EmailMessage.Status.CANCELED,
            error_message="Cooling down",
        )
        return False
    else:
        email_message_send_task.delay(e.id)
        return True


def email_message_send(*, email_message: EmailMessage) -> None:
    """Send an email_message immediately. Normally called by a celery task."""
    if email_message.status != constants.EmailMessage.Status.READY:
        raise RuntimeError(
            f"EmailMessage.id={email_message.id} email_message_send called on an email that is not status=READY. Did you run email_message_queue()"
        )
    email_message_update(
        instance=email_message, status=constants.EmailMessage.Status.PENDING
    )
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
                f"EmailMessage.id={email_message.id} template not found {html_template_name}"
            )

        encoding = settings.DEFAULT_CHARSET
        from_email = sanitize_address(
            (email_message.sender_name, email_message.sender_email), encoding
        )
        to = [
            sanitize_address((email_message.to_name, email_message.to_email), encoding),
        ]

        if email_message.reply_to_email:
            reply_to = [
                sanitize_address(
                    (email_message.reply_to_name, email_message.reply_to_email),
                    encoding,
                )
            ]
        else:
            reply_to = None

        django_email_message = EmailMultiAlternatives(
            subject=email_message.subject,
            from_email=from_email,
            to=to,
            body=msg,
            reply_to=reply_to,
        )
        if html_msg:
            django_email_message.attach_alternative(html_msg, "text/html")

        for attachment in email_message.attachments.all():
            django_email_message.attach(
                attachment.filename, attachment.file.read(), attachment.mimetype
            )
        if email_message.postmark_message_stream:
            django_email_message.message_stream = (  # type: ignore
                email_message.postmark_message_stream
            )

        if global_setting_get_value("disable_outbound_email"):
            raise RuntimeError("GlobalSetting disable_outbound_email is True")
        else:
            message_ids = django_email_message.send()

            # Postmark has a setting for returning MessageIDs
            if isinstance(message_ids, list):
                if len(message_ids) == 1:
                    email_message.message_id = message_ids[0]

    except Exception as e:
        email_message_update(
            instance=email_message,
            status=constants.EmailMessage.Status.ERROR,
            error_message=repr(e),
        )
        logger.exception(
            f"EmailMessage.id={email_message.id} Exception caught in send_email_message"
        )
    else:
        email_message_update(
            instance=email_message,
            status=constants.EmailMessage.Status.SENT,
            sent_at=timezone.now(),
        )


def email_message_create(save=False, **kwargs) -> EmailMessage:
    # By default, we don't persist the email_message because often it is
    # not ready until email_message_prepare is called on it.
    return model_create(klass=EmailMessage, save=save, **kwargs)


def email_message_update(*, instance: EmailMessage, **kwargs) -> EmailMessage:
    return model_update(instance=instance, data=kwargs)


def email_message_duplicate(*, original: EmailMessage) -> EmailMessage:
    """Duplicate an EmailMessage and return the new EmailMessage."""
    duplicate = model_duplicate(instance=original)

    email_message_update(
        instance=duplicate,
        status=constants.EmailMessage.Status.NEW,
        error_message="",
        message_id=None,
        sent_at=None,
    )

    email_message_prepare(email_message=duplicate)

    for attachment in original.attachments.all():
        email_message_attach(
            email_message=duplicate,
            file=attachment.file,
            filename=attachment.filename,
            mimetype=attachment.mimetype,
        )

    return duplicate


def email_message_attachment_create(**kwargs) -> EmailMessageAttachment:
    return model_create(klass=EmailMessageAttachment, **kwargs)


def email_message_attachment_update(
    *, instance: EmailMessageAttachment, **kwargs
) -> EmailMessageAttachment:
    return model_update(instance=instance, data=kwargs)


def email_message_webhook_create_from_request(
    *, body: str, headers: dict
) -> EmailMessageWebhook:
    """Create an EmailMessageWebhook from a request object."""
    payload = utils.validate_request_body_json(body=body)
    if type(payload) != dict:
        raise ApplicationError("Invalid payload")

    headers_processed = {}
    for key in headers:
        value = headers[key]
        if isinstance(value, str):
            headers_processed[key] = value

    webhook = email_message_webhook_create(
        body=payload,
        headers=headers_processed,
        status=constants.EmailMessageWebhook.Status.NEW,
    )
    logger.info(f"EmailMessageWebhook.id={webhook.id} received")

    return webhook


def email_message_webhook_create(**kwargs) -> EmailMessageWebhook:
    return model_create(klass=EmailMessageWebhook, **kwargs)


def email_message_webhook_update(
    *, instance: EmailMessageWebhook, **kwargs
) -> EmailMessageWebhook:
    return model_update(instance=instance, data=kwargs)


def email_message_webhook_process(
    *, email_message_webhook: EmailMessageWebhook
) -> None:
    webhook = email_message_webhook
    try:
        if webhook.status != constants.EmailMessageWebhook.Status.NEW:
            raise RuntimeError(
                f"EmailMessageWebhook.id={webhook.id} process_email_message_webhook called on a webhook that is not status=NEW"
            )
        email_message_webhook_update(
            instance=webhook, status=constants.EmailMessageWebhook.Status.PENDING
        )

        # Store the type
        if "RecordType" in webhook.body:
            email_message_webhook_update(
                instance=webhook, type=webhook.body["RecordType"]
            )

        # Find the related EmailMessage and connect it
        if "MessageID" in webhook.body:
            email_message = selectors.email_message_list(
                message_id=webhook.body["MessageID"]
            ).first()
            if email_message:
                webhook.email_message = email_message
                if webhook.type in constants.WEBHOOK_TYPE_TO_EMAIL_STATUS:
                    # Make sure this is the most recent webhook, in case it arrived out of order.
                    all_ts = []
                    for other_webhook in selectors.email_message_webhook_list(
                        email_message=email_message
                    ):
                        ts_key = constants.WEBHOOK_TYPE_TO_TIMESTAMP[other_webhook.type]
                        ts = other_webhook.body[ts_key]
                        ts = ts.replace("Z", "+00:00")
                        all_ts.append(datetime.fromisoformat(ts))
                    all_ts.sort()

                    ts_key = constants.WEBHOOK_TYPE_TO_TIMESTAMP[webhook.type]
                    ts = webhook.body[ts_key]
                    ts = ts.replace("Z", "+00:00")
                    ts_dt = datetime.fromisoformat(ts)
                    if len(all_ts) == 0 or all_ts[-1] < ts_dt:
                        new_status = constants.WEBHOOK_TYPE_TO_EMAIL_STATUS[
                            webhook.type
                        ]
                        email_message_update(instance=email_message, status=new_status)

        email_message_webhook_update(
            instance=webhook, status=constants.EmailMessageWebhook.Status.PROCESSED
        )
        logger.debug(f"EmailMessageWebhook.id={webhook.id} processed")
    except Exception as e:
        logger.exception(f"EmailMessageWebhook.id={webhook.id} in error state")
        email_message_webhook_update(
            instance=webhook,
            status=constants.EmailMessageWebhook.Status.ERROR,
            note=traceback.format_exc(),
        )


def org_invitation_validate_new(
    *, org: Org, created_by: UserType, org_invitation: OrgInvitation
) -> OrgInvitation:
    """Validate that an OrgInvitation is ready to be created and sent."""
    if not org_invitation._state.adding:
        raise RuntimeError(
            "org_invitation_send service must be called with a new object"
        )
    if not org_invitation.email:
        raise RuntimeError(
            "org_invitation_send service must be called with an OrgInvitation that has an email"
        )

    if selectors.org_invitation_list(org=org, email=org_invitation.email).exists():
        raise ApplicationWarning(
            f"{org_invitation.email} already has an invitation to {org}."
        )

    if selectors.org_user_list(org=org, user__email=org_invitation.email).exists():
        raise ApplicationError(f"{org_invitation.email} is already a member of {org}.")

    # This will blow up if there are problems because we don't catch ValidationError.
    # But that is fine as there should never be problems and if there are we want to know.
    return org_invitation_update(
        instance=org_invitation, org=org, created_by=created_by
    )


def org_invitation_send(*, org_invitation: OrgInvitation) -> None:
    """Send a new OrgInvitation."""
    assert settings.SITE_CONFIG["default_from_email"] is not None
    sender_email = settings.SITE_CONFIG["default_from_email"]
    sender_name = utils.get_email_display_name(
        org_invitation.created_by,
        header="From",
        email=sender_email,
        suffix=f"via {settings.SITE_CONFIG['name']}",
    )

    reply_to_name = utils.get_email_display_name(
        org_invitation.created_by, header="Reply-To"
    )
    reply_to_email = org_invitation.created_by.email

    email_message = email_message_create(
        created_by=org_invitation.created_by,
        org=org_invitation.org,
        subject=f"Invitation to join {org_invitation.org.name} on {settings.SITE_CONFIG['name']}",
        to_email=org_invitation.email,
        sender_name=sender_name,
        sender_email=sender_email,
        reply_to_name=reply_to_name,
        reply_to_email=reply_to_email,
        template_prefix="core/email/org_invitation",
        template_context={
            "org_name": org_invitation.org.name,
            "inviter": org_invitation.created_by.name,
            "action_url": "",
        },
    )
    email_message_queue(email_message=email_message)
    org_invitation.email_messages.add(email_message)


def org_invitation_resend(*, org: Org, uuid: str) -> None:
    """Resend an OrgInvitation."""
    org_invitation = selectors.org_invitation_list(org=org, uuid=uuid).get()
    org_invitation_send(org_invitation=org_invitation)


def org_switch(*, request: HttpRequest, slug: str) -> None:
    """Switch a user to a different Org."""
    org = selectors.org_list(slug=slug, users=request.user, is_active=True).get()

    assert hasattr(request, "org"), "org is always set on request in the middleware"
    request.org = org


def org_user_create(*, org: Org, user: UserType) -> OrgUser:
    return model_create(klass=OrgUser, org=org, user=user)


def org_create(**kwargs) -> Org:
    """Create an Org and return the Org."""
    org = model_create(klass=Org, **kwargs)

    # If owner isn't an OrgUser, create one.
    if not selectors.org_user_list(org=org, user=org.owner).exists():
        org_user_create(org=org, user=org.owner)

    return org


def org_update(*, instance: Org, **kwargs) -> Org:
    """Update an Org and return the Org."""

    # If this is a personal org, activate the AutoSlugField's overwrite flag.
    # This makes it so that the slug will auto-reference the name field.
    if instance.is_personal:
        instance._meta.get_field("slug").overwrite = True

    org = model_update(instance=instance, data=kwargs)

    # Reset the slug overwrite flag to its default value.
    instance._meta.get_field("slug").overwrite = False

    # If owner isn't an OrgUser, create one.
    if not selectors.org_user_list(org=org, user=org.owner).exists():
        org_user_create(org=org, user=org.owner)

    return org


def plan_create(*, instance: Optional[Plan] = None, **kwargs) -> Plan:
    """Create a Plan and return the Plan, dealing with setting and unsetting of is_default."""

    # If is_default is set on kwargs, is_default should be set to that.
    is_default = False
    try:
        is_default = kwargs["is_default"]
    except KeyError:
        # If is_default is not set on kwargs, but instance is set and is_default is True, is_default should be set to True.
        if instance and instance.is_default is True:
            is_default = True

    with transaction.atomic():
        # If this plan is set to the default, unset default on all other plans.
        if is_default:
            count = model_bulk_update(
                qs=selectors.plan_list(is_default=True), is_default=False
            )
            if count:
                logger.warning(
                    f"Unset is_default on {count} Plans. This is okay if you meant to change the default Plan."
                )
        plan = model_create(klass=Plan, instance=instance, **kwargs)
    return plan


def plan_update(*, instance: Plan, **kwargs) -> Plan:
    """Update a Plan and return the Plan."""
    # If is_default is set on kwargs, is_default should be set to that.
    is_default = False
    try:
        is_default = kwargs["is_default"]
    except KeyError:
        # If is_default is not set on kwargs, but instance is set and is_default is True, is_default should be set to True.
        if instance and instance.is_default is True:
            is_default = True

    with transaction.atomic():
        # If this plan is set to the default, unset default on all other plans.
        if is_default:
            count = model_bulk_update(
                qs=selectors.plan_list(is_default=True).exclude(pk=instance.pk),
                is_default=False,
            )
            if count:
                logger.warning(
                    f"Unset is_default on {count} Plans. This is okay if you meant to change the default Plan."
                )
        plan = model_update(instance=instance, data=kwargs)
    return plan


def global_setting_update(*, instance: GlobalSetting, **kwargs) -> GlobalSetting:
    """Update a GlobalSetting and return the GlobalSetting."""
    return model_update(instance=instance, data=kwargs)


def org_user_update(*, instance: OrgUser, **kwargs) -> OrgUser:
    """Update an OrgUser and return the OrgUser."""
    return model_update(instance=instance, data=kwargs)


def org_invitation_update(*, instance: OrgInvitation, **kwargs) -> OrgInvitation:
    """Update an OrgInvitation and return the OrgInvitation."""
    return model_update(instance=instance, data=kwargs)


def org_setting_update(*, instance: OrgSetting, **kwargs) -> OrgSetting:
    """Update an OrgSetting and return the OrgSetting."""
    return model_update(instance=instance, data=kwargs)


def plan_org_setting_update(*, instance: PlanOrgSetting, **kwargs) -> PlanOrgSetting:
    """Update a PlanOrgSetting and return the PlanOrgSetting."""
    return model_update(instance=instance, data=kwargs)


def overridden_org_setting_update(
    *, instance: OverriddenOrgSetting, **kwargs
) -> OverriddenOrgSetting:
    """Update an OverriddenOrgSetting and return the OverriddenOrgSetting."""
    return model_update(instance=instance, data=kwargs)


def org_user_setting_update(*, instance: OrgUserSetting, **kwargs) -> OrgUserSetting:
    return model_update(instance=instance, data=kwargs)


def org_user_org_user_setting_update(
    *, instance: OrgUserOrgUserSetting, **kwargs
) -> OrgUserOrgUserSetting:
    return model_update(instance=instance, data=kwargs)


def org_user_setting_default_update(
    *, instance: OrgUserSettingDefault, **kwargs
) -> OrgUserSettingDefault:
    return model_update(instance=instance, data=kwargs)


def model_update(
    *,
    instance: BaseModelType,
    save=True,
    data: Dict[str, Any],
) -> BaseModelType:
    """Update a model instance with the provided data and return the instance. This does not
    reset any fields on the instance, so if updates have already been made to the instance, they
    will stick unless overriden by the data."""
    m2m_data = {}

    model_fields = {field.name: field for field in instance._meta.get_fields()}

    for field in data:
        # If field is not an actual model field, raise an error
        model_field = model_fields.get(field)

        assert (
            model_field is not None
        ), f"{field} is not part of {instance.__class__.__name__} fields."

        # If we have m2m field, handle differently
        if isinstance(model_field, models.ManyToManyField):
            m2m_data[field] = data[field]
            continue

        setattr(instance, field, data[field])

    if save:
        instance.full_clean()
        instance._allow_save = True
        instance.save()
    elif len(m2m_data) > 0:
        raise RuntimeError(
            "Cannot save m2m data without saving the instance. Set save=True."
        )

    for field_name, value in m2m_data.items():
        related_manager = getattr(instance, field_name)
        related_manager.set(value)

    return instance


def model_bulk_update(*, qs: QuerySet, **kwargs) -> int:
    """Bulk update a set of instances and return the number of instances updated."""
    return qs.update(**kwargs)


def global_setting_get_value(slug: str) -> bool | int:
    """Get a GlobalSetting, creating it as False if it does not exist."""
    try:
        setting = selectors.global_setting_list(slug=slug).get()
    except GlobalSetting.DoesNotExist:
        setting = global_setting_create(
            slug=slug, type=constants.SettingType.BOOL, value=0
        )

    return setting.value


def org_get_setting_value(*, org: Org, slug: str) -> bool | int:
    # See test_org_settings.py for an explanation of how this works.
    try:
        setting = selectors.org_setting_list(slug=slug).get()
    except OrgSetting.DoesNotExist:
        setting = org_setting_create(
            slug=slug, type=constants.SettingType.BOOL, default=0
        )

    try:
        overridden_org_setting = selectors.overridden_org_setting_list(
            org=org, setting=setting
        ).get()
        best = overridden_org_setting.value
    except OverriddenOrgSetting.DoesNotExist:
        plan = selectors.org_get_plan(org=org)
        try:
            plan_org_setting = selectors.plan_org_setting_list(
                plan=plan, setting=setting
            ).get()
        except PlanOrgSetting.DoesNotExist:
            plan_org_setting = plan_org_setting_create(
                plan=plan, setting=setting, value=setting.default
            )
        best = plan_org_setting.value

    if setting.type == constants.SettingType.BOOL:
        return bool(best)

    return best


def org_user_get_setting_value(*, org_user: OrgUser, slug: str) -> bool | int:
    try:
        setting = selectors.org_user_setting_list(slug=slug).get()
    except OrgUserSetting.DoesNotExist:
        setting = org_user_setting_create(
            slug=slug, type=constants.SettingType.BOOL, default=0, owner_value=1
        )

    # Short-circuit if the OrgUser is the Org owner.
    if org_user.org.owner == org_user.user:
        if setting.type == constants.SettingType.BOOL:
            return bool(setting.owner_value)
        else:
            return setting.owner_value

    try:
        org_user_org_user_setting = selectors.org_user_org_user_setting_list(
            org_user=org_user, setting=setting
        ).get()
        best = org_user_org_user_setting.value
    except OrgUserOrgUserSetting.DoesNotExist:
        try:
            org_user_setting_default = selectors.org_user_setting_default_list(
                org=org_user.org, setting=setting
            ).get()
        except OrgUserSettingDefault.DoesNotExist:
            org_user_setting_default = org_user_setting_default_create(
                org=org_user.org, setting=setting, value=setting.default
            )
        best = org_user_setting_default.value

    if setting.type == constants.SettingType.BOOL:
        return bool(best)

    return best


def global_setting_create(**kwargs) -> GlobalSetting:
    return model_create(klass=GlobalSetting, **kwargs)


def org_setting_create(**kwargs) -> OrgSetting:
    return model_create(klass=OrgSetting, **kwargs)


def org_user_setting_create(**kwargs) -> OrgUserSetting:
    return model_create(klass=OrgUserSetting, **kwargs)


def org_user_setting_default_create(**kwargs) -> OrgUserSettingDefault:
    return model_create(klass=OrgUserSettingDefault, **kwargs)


def plan_org_setting_create(**kwargs) -> PlanOrgSetting:
    return model_create(klass=PlanOrgSetting, **kwargs)


def org_invitation_create(**kwargs) -> OrgInvitation:
    return model_create(klass=OrgInvitation, **kwargs)


def overridden_org_setting_create(**kwargs) -> OverriddenOrgSetting:
    return model_create(klass=OverriddenOrgSetting, **kwargs)


def org_user_org_user_setting_create(**kwargs) -> OrgUserOrgUserSetting:
    return model_create(klass=OrgUserOrgUserSetting, **kwargs)


def model_create(
    *,
    klass: Type[BaseModelType],
    instance: Optional[BaseModelType] = None,
    save=True,
    **kwargs: Union[Model, str, bool],
):
    """Create a model instance and return the model instance.
    If an instance is passed, don't create a new instance, but ensure
    that the passed instance does not yet exist in the database."""

    if instance:
        if not instance._state.adding:
            raise RuntimeError(
                f"{instance.__class__.__name__} instance is not new. Did you mean to call model_update()?"
            )
    else:
        instance = klass(**kwargs)

    return model_update(instance=instance, save=save, data=kwargs)


def model_duplicate(*, instance: BaseModelType) -> BaseModelType:
    """Duplicate a model instance and return the new model instance."""
    # Get a new handle to the instance to avoid mutating the original.
    duplicate = selectors.model_list(klass=instance.__class__, pk=instance.pk).get()

    duplicate.pk = None
    duplicate.uuid = uuid4()
    duplicate._state.adding = True
    duplicate.full_clean()
    duplicate._allow_save = True
    duplicate.save()
    return duplicate
