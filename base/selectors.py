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
    OUSetting,
    OUSettingDefault,
    OrgUserOUSetting,
    Plan,
    PlanOrgSetting,
)


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


def org_get_setting(*, org: Org, slug: str) -> bool | int:
    # See test_org_settings.py for an explanation of how this works.
    # FIXME use selectors

    setting, _ = OrgSetting.objects.get_or_create(
        slug=slug, defaults={"type": constants.SettingType.BOOL, "default": 0}
    )

    overridden_org_setting = OverriddenOrgSetting.objects.filter(
        org=org, setting=setting
    ).first()

    if overridden_org_setting:
        best = overridden_org_setting.value
    else:
        plan = org_get_plan(org=org)
        plan_org_setting, _ = PlanOrgSetting.objects.get_or_create(
            plan=plan,
            setting=setting,
            defaults={"value": setting.default},
        )
        best = plan_org_setting.value

    if setting.type == constants.SettingType.BOOL:
        return bool(best)

    return best


def org_user_get_setting(*, org_user: OrgUser, slug: str) -> bool | int:
    # FIXME use selectors

    setting, _ = OUSetting.objects.get_or_create(
        slug=slug,
        defaults={
            "type": constants.SettingType.BOOL,
            "default": 0,
            "owner_value": 1,
        },
    )

    # Short-circuit if the OrgUser is the Org owner.
    if org_user.org.owner == org_user.user:
        if setting.type == constants.SettingType.BOOL:
            return bool(setting.owner_value)
        else:
            return setting.owner_value

    org_user_ou_setting = OrgUserOUSetting.objects.filter(
        org_user=org_user, setting=setting
    ).first()
    if org_user_ou_setting:
        best = org_user_ou_setting.value
    else:
        ou_setting_default, _ = OUSettingDefault.objects.get_or_create(
            org=org_user.org, setting=setting, defaults={"value": setting.default}
        )
        best = ou_setting_default.value

    if setting.type == constants.SettingType.BOOL:
        return bool(best)

    return best


def model_list(
    *, klass: Type[ModelType], **kwargs: Union[Model, str, bool]
) -> QuerySet[ModelType]:
    return klass.objects.filter(**kwargs)
