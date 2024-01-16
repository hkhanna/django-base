from typing import Union, Type

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

from core.types import BaseModelType, UserType

from .models import (
    GlobalSetting,
    Org,
    OrgInvitation,
    OrgSetting,
    OrgUser,
    OverriddenOrgSetting,
    OrgUserSetting,
    OrgUserSettingDefault,
    OrgUserOrgUserSetting,
    Plan,
    PlanOrgSetting,
    EmailMessage,
    EmailMessageAttachment,
    EmailMessageWebhook,
    Event,
)

User = get_user_model()


def email_message_list(**kwargs) -> QuerySet[EmailMessage]:
    return model_list(klass=EmailMessage, **kwargs)


def email_message_attachment_list(**kwargs) -> QuerySet[EmailMessageAttachment]:
    return model_list(klass=EmailMessageAttachment, **kwargs)


def email_message_webhook_list(**kwargs) -> QuerySet[EmailMessageWebhook]:
    return model_list(klass=EmailMessageWebhook, **kwargs)


def event_list(**kwargs) -> QuerySet[Event]:
    return model_list(klass=Event, **kwargs)


def global_setting_list(**kwargs) -> QuerySet[GlobalSetting]:
    return model_list(klass=GlobalSetting, **kwargs)


def org_list(**kwargs) -> QuerySet[Org]:
    return model_list(klass=Org, **kwargs)


def org_invitation_list(**kwargs) -> QuerySet[OrgInvitation]:
    return model_list(klass=OrgInvitation, **kwargs)


def org_user_list(**kwargs) -> QuerySet[OrgUser]:
    return model_list(klass=OrgUser, **kwargs)


def org_get_plan(*, org: Org) -> Plan:
    """Returns an Org's primary_plan or default_plan as a function of current_period_end."""
    if org.current_period_end and timezone.now() > org.current_period_end:
        return org.default_plan
    return org.primary_plan


def org_user_setting_list(**kwargs) -> QuerySet[OrgUserSetting]:
    return model_list(klass=OrgUserSetting, **kwargs)


def org_user_org_user_setting_list(**kwargs) -> QuerySet[OrgUserOrgUserSetting]:
    return model_list(klass=OrgUserOrgUserSetting, **kwargs)


def org_user_setting_default_list(**kwargs) -> QuerySet[OrgUserSettingDefault]:
    return model_list(klass=OrgUserSettingDefault, **kwargs)


def plan_list(**kwargs) -> QuerySet[Plan]:
    return model_list(klass=Plan, **kwargs)


def plan_org_setting_list(**kwargs) -> QuerySet[PlanOrgSetting]:
    return model_list(klass=PlanOrgSetting, **kwargs)


def overridden_org_setting_list(**kwargs) -> QuerySet[OverriddenOrgSetting]:
    return model_list(klass=OverriddenOrgSetting, **kwargs)


def org_setting_list(**kwargs) -> QuerySet[OrgSetting]:
    return model_list(klass=OrgSetting, **kwargs)


def user_list(**kwargs) -> QuerySet[UserType]:
    return User._default_manager.filter(**kwargs)


def model_list(*, klass: Type[BaseModelType], **kwargs) -> QuerySet:
    return klass._default_manager.filter(**kwargs)
