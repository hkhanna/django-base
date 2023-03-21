"""Tests related to settings for Orgs, OrgUsers, and Plans."""
import pytest
from pytest_django.asserts import assertRaisesMessage
from django.core.exceptions import ValidationError
from datetime import timedelta
from freezegun import freeze_time
from ..models import (
    OrgSetting,
    PlanOrgSetting,
    OverriddenOrgSetting,
    OUSetting,
    OUSettingDefault,
    OrgUserOUSetting,
)
from base import constants

# The general philosophy is this.
# There are 2 types of settings, settings for an Org (OrgSetting) and settings for an OrgUser (OUSetting).
# They are related to Orgs, OrgUsers and Plans in different ways.
# - OrgSettings are primarily related to a payment Plan. An Org may override an OrgSetting, in which case it will not look to the Plan for that OrgSetting.
# - If a Plan is queried for an OrgSetting, and that OrgSetting is not set on the Plan, it will materialize the setting on the Plan with the OrgSetting's default.
# - OUSettings should have defaults set by the Org. If an Org is accessed for an OUSetting default and it's not there, it will materialize it on the Org.
#    - At this point, it doesn't seem useful to attach OUSetting defaults to a Plan, so we don't. We can easily change this down the road though.
#    - We set an owner_value on the base OUSetting that is always used for the Org owner, who is kind of a superuser.
# - If a setting does not exist but is queried, that setting will autocreate with a default of False and an owner_value of True.

# A one-time payment situation would probably only use the default Plan and override OrgSettings as the purchase is made.
# Each setting stores its value as an integer, but if the type is set to `bool` instead of `int`, it will report it as True or False.


@pytest.fixture
def org_setting():
    return OrgSetting.objects.create(
        slug="for-test", default=5, type=constants.SettingType.INT
    )


@pytest.fixture
def ou_setting():
    return OUSetting.objects.create(
        slug="for-test", default=5, owner_value=100, type=constants.SettingType.INT
    )


# -- OrgSettings -- #


def test_org_get_setting_noexist(org):
    """Org.get_setting() will create an OrgSetting with a default of False if it is accessed but does not exist"""
    assert OrgSetting.objects.count() == 0  # No OrgSettings yet.

    result = org.get_setting("for-test")
    settings = OrgSetting.objects.all()
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "for-test"
    assert setting.default == 0
    assert setting.type == constants.SettingType.BOOL
    assert result is False


def test_org_get_setting_noplan(org, org_setting):
    """Org.get_setting() will materialize an OrgSetting on the Plan if it isn't already on the Plan"""
    result = org.get_setting("for-test")
    assert OrgSetting.objects.count() == 1
    # Setting shouldn't change
    assert org_setting.slug == "for-test"
    assert org_setting.default == 5
    assert org_setting.type == constants.SettingType.INT
    assert result == 5

    # Materialized on Plan
    assert org.primary_plan.plan_org_settings.first().setting == org_setting


def test_org_get_setting_plan(org, org_setting):
    """Org.get_setting() in the normal case will retrieve the OrgSetting from the Plan"""
    PlanOrgSetting.objects.create(plan=org.primary_plan, setting=org_setting, value=10)

    result = org.get_setting("for-test")
    assert OrgSetting.objects.count() == 1
    assert OrgSetting.objects.first().default == 5  # No change
    assert PlanOrgSetting.objects.count() == 1
    assert PlanOrgSetting.objects.first().value == 10  # No change
    assert result == 10


def test_org_get_setting_override(org, org_setting):
    """Org.get_setting() will prioritize any OverriddenOrgSettings"""
    PlanOrgSetting.objects.create(plan=org.primary_plan, setting=org_setting, value=10)
    OverriddenOrgSetting.objects.create(org=org, setting=org_setting, value=20)

    result = org.get_setting("for-test")
    assert OrgSetting.objects.count() == 1
    assert OrgSetting.objects.first().default == 5  # No change
    assert PlanOrgSetting.objects.count() == 1
    assert PlanOrgSetting.objects.first().value == 10  # No change
    assert OverriddenOrgSetting.objects.count() == 1
    assert OverriddenOrgSetting.objects.first().value == 20  # No change
    assert result == 20


def test_org_get_setting_plan_expired(org, org_setting):
    """If Org.current_period_end is expired, Org.get_setting() should look to Org.default_plan"""
    PlanOrgSetting.objects.create(plan=org.primary_plan, setting=org_setting, value=10)
    with freeze_time(org.current_period_end + timedelta(seconds=1)):
        result = org.get_setting("for-test")
        assert OrgSetting.objects.count() == 1
        assert OrgSetting.objects.first().default == 5  # No change
        assert (
            PlanOrgSetting.objects.count() == 2
        )  # A setting was created on the default_plan
        assert result == 5  # Uses the default

        default_setting = org.default_plan.plan_org_settings.first()
        default_setting.value = 30
        default_setting.full_clean()
        default_setting.save()
        result = org.get_setting("for-test")
        assert result == 30  # Use the specified

    result = org.get_setting("for-test")
    assert result == 10  # Use the primary plan's now that we're not expired.


def test_org_get_setting_plan_never_expires(org, org_setting):
    """If Org.current_period_end is None, the plan never expires."""
    PlanOrgSetting.objects.create(plan=org.primary_plan, setting=org_setting, value=10)
    org.current_period_end = None
    org.full_clean()
    org.save()
    result = org.get_setting("for-test")
    assert result == 10


def test_org_setting_boolean(org):
    """OrgSettings of type bool may only have a value of 0 or 1."""
    org_setting = OrgSetting.objects.create(
        slug="for-test", type=constants.SettingType.BOOL, default=0
    )
    org_setting.default = 1
    org_setting.full_clean()
    org_setting.save()  # OK

    with assertRaisesMessage(ValidationError, "0 or 1"):
        org_setting.default = 2
        org_setting.full_clean()

    with assertRaisesMessage(ValidationError, "0 or 1"):
        PlanOrgSetting(plan=org.primary_plan, setting=org_setting, value=2).full_clean()

    with assertRaisesMessage(ValidationError, "0 or 1"):
        OverriddenOrgSetting(org=org, setting=org_setting, value=2).full_clean()


# -- OUSettings -- #


def test_ou_get_setting_noexist(ou):
    """OrgUser.get_setting() will create a boolean OUSetting with a default of 0 and owner_value of 1 if it is accessed but does not exist"""
    assert OUSetting.objects.count() == 0  # No OUSettings yet.

    result = ou.get_setting("for-test")
    settings = OUSetting.objects.all()
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "for-test"
    assert setting.default == 0
    assert setting.owner_value == 1
    assert setting.type == constants.SettingType.BOOL
    assert result is False


def test_ou_get_setting_materialize_org_defaults(ou, ou_setting):
    """OrgUser.get_setting() will materialize OUSettingDefaults on the Org if there is no direct setting on the OrgUser"""
    result = ou.get_setting("for-test")

    assert OUSetting.objects.count() == 1

    # Setting shouldn't change
    assert ou_setting.slug == "for-test"
    assert ou_setting.default == 5
    assert ou_setting.type == constants.SettingType.INT
    assert result == 5

    # Materialized on Org
    assert ou.org.ou_setting_defaults.first().setting == ou_setting


def test_ou_get_setting_defaults(ou, ou_setting):
    """OrgUser.get_setting() in the normal case will retrieve the OrgSetting from the OuSettingDefaults (but not materialize the setting on OrgUser)"""
    OUSettingDefault.objects.create(org=ou.org, setting=ou_setting, value=10)

    result = ou.get_setting("for-test")
    assert OUSetting.objects.count() == 1
    assert OUSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOUSetting.objects.count() == 0  # Did not materialize on OrgUser

    assert result == 10


def test_ou_get_setting(ou, ou_setting):
    """OrgUser.get_setting() will prioritize a direct setting on the OrgUser"""
    OUSettingDefault.objects.create(org=ou.org, setting=ou_setting, value=10)
    OrgUserOUSetting.objects.create(org_user=ou, setting=ou_setting, value=20)

    result = ou.get_setting("for-test")
    assert OUSetting.objects.count() == 1
    assert OUSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOUSetting.objects.count() == 1
    assert OrgUserOUSetting.objects.first().value == 20  # No change

    assert result == 20


def test_ou_setting_boolean(ou):
    """OUSettings of type bool may only have a value of 0 or 1."""
    ou_setting = OUSetting.objects.create(
        slug="for-test", type=constants.SettingType.BOOL, default=0, owner_value=1
    )
    ou_setting.default = 1
    ou_setting.full_clean()
    ou_setting.save()  # OK

    with assertRaisesMessage(ValidationError, "0 or 1"):
        ou_setting.default = 2
        ou_setting.full_clean()

    ou_setting.refresh_from_db()

    with assertRaisesMessage(ValidationError, "0 or 1"):
        ou_setting.owner_value = 2
        ou_setting.full_clean()

    with assertRaisesMessage(ValidationError, "0 or 1"):
        OUSettingDefault(org=ou.org, setting=ou_setting, value=2).full_clean()

    with assertRaisesMessage(ValidationError, "0 or 1"):
        OrgUserOUSetting(org_user=ou, setting=ou_setting, value=2).full_clean()


def test_ou_owner(org, ou, ou_setting):
    """OrgUser.get_setting() where the OrgUser is the owner always pulls from OUSetting.owner_value."""
    org.owner = ou.user
    org.full_clean()
    org.save()

    OUSettingDefault.objects.create(org=ou.org, setting=ou_setting, value=10)
    OrgUserOUSetting.objects.create(org_user=ou, setting=ou_setting, value=20)

    result = ou.get_setting("for-test")
    assert OUSetting.objects.count() == 1
    assert OUSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOUSetting.objects.count() == 1
    assert OrgUserOUSetting.objects.first().value == 20  # No change

    assert result == 100