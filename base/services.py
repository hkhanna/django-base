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
from datetime import datetime, timedelta
from importlib import import_module
from typing import List, Optional, Union, Dict, Any, Type

from django.conf import settings
from django.http import HttpRequest
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_str
from django.db import models, transaction
from django.db.models import Model, QuerySet

from . import selectors, tasks, utils, constants
from .exceptions import *
from .models import (
    EmailMessage,
    EmailMessageWebhook,
    Event,
    Org,
    OrgInvitation,
    OrgSetting,
    OUSetting,
    OUSettingDefault,
    OrgUserOUSetting,
    OrgUser,
    Plan,
    PlanOrgSetting,
    OverriddenOrgSetting,
)
from .types import ModelType, UserType

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


def event_create(**kwargs) -> Event:
    return model_create(klass=Event, **kwargs)


def event_update(instance: Event, **kwargs) -> Event:
    return model_update(instance=instance, data=kwargs)


def email_message_create(**kwargs) -> EmailMessage:
    """Create an EmailMessage object."""
    email_message = EmailMessage(**kwargs)
    email_message.full_clean()
    email_message.save()
    return email_message


def email_message_update(instance: EmailMessage, **kwargs) -> EmailMessage:
    return model_update(instance=instance, data=kwargs)


class EmailMessageService:
    """Service for sending emails."""

    def __init__(self, **kwargs: Union[str, dict, UserType, Org]) -> None:
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

    def email_message_send(
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
    """Create an EmailMessageWebhook."""
    email_message_webhook = EmailMessageWebhook(**kwargs)
    email_message_webhook.full_clean()
    email_message_webhook.save()
    return email_message_webhook


def email_message_webhook_update(
    *, instance: EmailMessageWebhook, **kwargs
) -> EmailMessageWebhook:
    return model_update(instance=instance, data=kwargs)


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

    org_invitation.org = org
    org_invitation.created_by = created_by

    # This will blow up if there are problems because we don't catch ValidationError.
    # But that is fine as there should never be problems and if there are we want to know.
    org_invitation.full_clean()
    org_invitation.save()
    return org_invitation


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

    service = EmailMessageService(
        created_by=org_invitation.created_by,
        org=org_invitation.org,
        subject=f"Invitation to join {org_invitation.org.name} on {settings.SITE_CONFIG['name']}",
        to_email=org_invitation.email,
        sender_name=sender_name,
        sender_email=sender_email,
        reply_to_name=reply_to_name,
        reply_to_email=reply_to_email,
        template_prefix="base/email/org_invitation",
        template_context={
            "org_name": org_invitation.org.name,
            "inviter": org_invitation.created_by.name,
            "action_url": "",
        },
    )
    service.email_message_send()
    org_invitation.save()
    org_invitation.email_messages.add(service.email_message)


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


def plan_create(**kwargs) -> Plan:
    """Create a Plan and return the Plan."""
    plan = Plan(**kwargs)

    with transaction.atomic():
        # If this plan is set to the default, unset default on all other plans.
        if plan.is_default:
            count = model_bulk_update(
                qs=selectors.plan_list(is_default=True), is_default=False
            )
            if count:
                logger.warning(
                    f"Unset is_default on {count} Plans. This is okay if you meant to change the default Plan."
                )
        plan.full_clean()
        plan.save()
    return plan


def plan_update(*, instance: Plan, **kwargs) -> Plan:
    """Update a Plan and return the Plan."""
    with transaction.atomic():
        # If this plan is set to the default, unset default on all other plans.
        if kwargs.get("is_default"):
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


def org_user_setting_update(*, instance: OUSetting, **kwargs) -> OUSetting:
    return model_update(instance=instance, data=kwargs)


def org_user_org_user_setting_update(
    *, instance: OrgUserOUSetting, **kwargs
) -> OrgUserOUSetting:
    return model_update(instance=instance, data=kwargs)


def org_user_setting_default_update(
    *, instance: OUSettingDefault, **kwargs
) -> OUSettingDefault:
    return model_update(instance=instance, data=kwargs)


def model_update(
    *,
    instance: ModelType,
    data: Dict[str, Any],
) -> ModelType:
    """
    Generic update service meant to be reused in local update services.

    For example:

    def user_update(*, user: User, data) -> User:
        user, has_updated = model_update(instance=user, data=data)

        // Do other actions with the user here

        return user

    Return value: Tuple with the following elements:
        1. The instance we updated.
        2. A boolean value representing whether we performed an update or not.

    Some important notes:

        - There's a strict assertion that all values in `fields` are actual fields in `instance`.
        - `data` can support m2m fields, which are handled after the update on `instance`.
    """
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

    instance.full_clean()
    instance.save()

    for field_name, value in m2m_data.items():
        related_manager = getattr(instance, field_name)
        related_manager.set(value)

    return instance


def model_bulk_update(*, qs: QuerySet, **kwargs) -> int:
    """Bulk update a set of Plans and return the number of Plans updated."""
    return qs.update(**kwargs)


def org_get_setting(*, org: Org, slug: str) -> bool | int:
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


def org_user_get_setting(*, org_user: OrgUser, slug: str) -> bool | int:
    try:
        setting = selectors.ou_setting_list(slug=slug).get()
    except OUSetting.DoesNotExist:
        setting = ou_setting_create(
            slug=slug, type=constants.SettingType.BOOL, default=0, owner_value=1
        )

    # Short-circuit if the OrgUser is the Org owner.
    if org_user.org.owner == org_user.user:
        if setting.type == constants.SettingType.BOOL:
            return bool(setting.owner_value)
        else:
            return setting.owner_value

    try:
        org_user_ou_setting = selectors.org_user_ou_setting_list(
            org_user=org_user, setting=setting
        ).get()
        best = org_user_ou_setting.value
    except OrgUserOUSetting.DoesNotExist:
        try:
            ou_setting_default = selectors.ou_setting_default_list(
                org=org_user.org, setting=setting
            ).get()
        except OUSettingDefault.DoesNotExist:
            ou_setting_default = ou_setting_default_create(
                org=org_user.org, setting=setting, value=setting.default
            )
        best = ou_setting_default.value

    if setting.type == constants.SettingType.BOOL:
        return bool(best)

    return best


def org_setting_create(**kwargs) -> OrgSetting:
    return model_create(klass=OrgSetting, **kwargs)


def ou_setting_create(**kwargs) -> OUSetting:
    return model_create(klass=OUSetting, **kwargs)


def ou_setting_default_create(**kwargs) -> OUSettingDefault:
    return model_create(klass=OUSettingDefault, **kwargs)


def plan_org_setting_create(**kwargs) -> PlanOrgSetting:
    return model_create(klass=PlanOrgSetting, **kwargs)


def org_invitation_create(**kwargs) -> OrgInvitation:
    return model_create(klass=OrgInvitation, **kwargs)


def overridden_org_setting_create(**kwargs) -> OverriddenOrgSetting:
    return model_create(klass=OverriddenOrgSetting, **kwargs)


def org_user_ou_setting_create(**kwargs) -> OrgUserOUSetting:
    return model_create(klass=OrgUserOUSetting, **kwargs)


def org_user_setting_create(**kwargs) -> OUSetting:
    return model_create(klass=OUSetting, **kwargs)


def org_user_org_user_setting_create(**kwargs) -> OrgUserOUSetting:
    return model_create(klass=OrgUserOUSetting, **kwargs)


def org_user_setting_default_create(**kwargs) -> OUSettingDefault:
    return model_create(klass=OUSettingDefault, **kwargs)


def model_create(
    *, klass: Type[ModelType], save=True, **kwargs: Union[Model, str, bool]
):
    """Create a model instance and return the model instance."""
    instance = klass(**kwargs)
    if save:
        instance.full_clean()
        instance.save()
    return instance
