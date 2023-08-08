"""Tests related to settings for Orgs, OrgUsers, and Plans."""
import pytest
from ...models import (
    OrgUserSetting,
    OUSettingDefault,
    OrgUserOrgUserSetting,
)
from base import constants, services


@pytest.fixture
def org_user_setting():
    return OrgUserSetting.objects.create(
        slug="for-test", default=5, owner_value=100, type=constants.SettingType.INT
    )


def test_ou_get_setting_noexist(ou):
    """org_user_get_setting() will create a boolean OrgUserSetting with a default of 0 and owner_value of 1 if it is accessed but does not exist"""
    assert OrgUserSetting.objects.count() == 0  # No OUSettings yet.

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    settings = OrgUserSetting.objects.all()
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "for-test"
    assert setting.default == 0
    assert setting.owner_value == 1
    assert setting.type == constants.SettingType.BOOL
    assert result is False


def test_ou_get_setting_materialize_org_defaults(ou, org_user_setting):
    """org_user_get_setting() will materialize OUSettingDefaults on the Org if there is no direct setting on the OrgUser"""
    result = services.org_user_get_setting(org_user=ou, slug="for-test")

    assert OrgUserSetting.objects.count() == 1

    # Setting shouldn't change
    assert org_user_setting.slug == "for-test"
    assert org_user_setting.default == 5
    assert org_user_setting.type == constants.SettingType.INT
    assert result == 5

    # Materialized on Org
    assert ou.org.ou_setting_defaults.first().setting == org_user_setting


def test_ou_get_setting_defaults(ou, org_user_setting):
    """org_user_get_setting() in the normal case will retrieve the OrgSetting from the OuSettingDefaults (but not materialize the setting on OrgUser)"""
    OUSettingDefault.objects.create(org=ou.org, setting=org_user_setting, value=10)

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    assert OrgUserSetting.objects.count() == 1
    assert OrgUserSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOrgUserSetting.objects.count() == 0  # Did not materialize on OrgUser

    assert result == 10


def test_ou_get_setting(ou, org_user_setting):
    """org_user_get_setting() will prioritize a direct setting on the OrgUser"""
    OUSettingDefault.objects.create(org=ou.org, setting=org_user_setting, value=10)
    OrgUserOrgUserSetting.objects.create(
        org_user=ou, setting=org_user_setting, value=20
    )

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    assert OrgUserSetting.objects.count() == 1
    assert OrgUserSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOrgUserSetting.objects.count() == 1
    assert OrgUserOrgUserSetting.objects.first().value == 20  # No change

    assert result == 20


def test_ou_owner(org, ou, org_user_setting):
    """org_user_get_setting() where the OrgUser is the owner always pulls from OUSetting.owner_value."""
    org.owner = ou.user
    org.full_clean()
    org.save()

    OUSettingDefault.objects.create(org=ou.org, setting=org_user_setting, value=10)
    OrgUserOrgUserSetting.objects.create(
        org_user=ou, setting=org_user_setting, value=20
    )

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    assert OrgUserSetting.objects.count() == 1
    assert OrgUserSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOrgUserSetting.objects.count() == 1
    assert OrgUserOrgUserSetting.objects.first().value == 20  # No change

    assert result == 100
