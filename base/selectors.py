from typing import Union, Type

from django.db.models import Model, QuerySet
from django.utils import timezone

from base.types import ModelType

from . import constants
from .models import (
    Org,
    OrgInvitation,
    OrgSetting,
    OrgUser,
    OverriddenOrgSetting,
    OrgUserSetting,
    OUSettingDefault,
    OrgUserOUSetting,
    Plan,
    PlanOrgSetting,
    EmailMessage,
    EmailMessageWebhook,
    Event,
)


def email_message_list(**kwargs) -> QuerySet[EmailMessage]:
    return model_list(klass=EmailMessage, **kwargs)


def email_message_webhook_list(**kwargs) -> QuerySet[EmailMessageWebhook]:
    return model_list(klass=EmailMessageWebhook, **kwargs)


def event_list(**kwargs) -> QuerySet[Event]:
    return model_list(klass=Event, **kwargs)


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


def org_user_ou_setting_list(**kwargs) -> QuerySet[OrgUserOUSetting]:
    return model_list(klass=OrgUserOUSetting, **kwargs)


def ou_setting_default_list(**kwargs) -> QuerySet[OUSettingDefault]:
    return model_list(klass=OUSettingDefault, **kwargs)


def plan_list(**kwargs) -> QuerySet[Plan]:
    return model_list(klass=Plan, **kwargs)


def plan_org_setting_list(**kwargs) -> QuerySet[PlanOrgSetting]:
    return model_list(klass=PlanOrgSetting, **kwargs)


def overridden_org_setting_list(**kwargs) -> QuerySet[OverriddenOrgSetting]:
    return model_list(klass=OverriddenOrgSetting, **kwargs)


def org_setting_list(**kwargs) -> QuerySet[OrgSetting]:
    return model_list(klass=OrgSetting, **kwargs)


def org_user_org_user_setting_list(**kwargs) -> QuerySet[OrgUserOUSetting]:
    return model_list(klass=OrgUserOUSetting, **kwargs)


def org_user_setting_default_list(**kwargs) -> QuerySet[OUSettingDefault]:
    return model_list(klass=OUSettingDefault, **kwargs)


def model_list(
    *, klass: Type[ModelType], **kwargs: Union[Model, str, bool]
) -> QuerySet[ModelType]:
    return klass.objects.filter(**kwargs)
