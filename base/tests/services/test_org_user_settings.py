"""Tests related to settings for Orgs, OrgUsers, and Plans."""
import pytest
from ...models import (
    OUSetting,
    OUSettingDefault,
    OrgUserOUSetting,
)
from base import constants, services


@pytest.fixture
def ou_setting():
    return OUSetting.objects.create(
        slug="for-test", default=5, owner_value=100, type=constants.SettingType.INT
    )


def test_ou_get_setting_noexist(ou):
    """org_user_get_setting() will create a boolean OUSetting with a default of 0 and owner_value of 1 if it is accessed but does not exist"""
    assert OUSetting.objects.count() == 0  # No OUSettings yet.

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    settings = OUSetting.objects.all()
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "for-test"
    assert setting.default == 0
    assert setting.owner_value == 1
    assert setting.type == constants.SettingType.BOOL
    assert result is False


def test_ou_get_setting_materialize_org_defaults(ou, ou_setting):
    """org_user_get_setting() will materialize OUSettingDefaults on the Org if there is no direct setting on the OrgUser"""
    result = services.org_user_get_setting(org_user=ou, slug="for-test")

    assert OUSetting.objects.count() == 1

    # Setting shouldn't change
    assert ou_setting.slug == "for-test"
    assert ou_setting.default == 5
    assert ou_setting.type == constants.SettingType.INT
    assert result == 5

    # Materialized on Org
    assert ou.org.ou_setting_defaults.first().setting == ou_setting


def test_ou_get_setting_defaults(ou, ou_setting):
    """org_user_get_setting() in the normal case will retrieve the OrgSetting from the OuSettingDefaults (but not materialize the setting on OrgUser)"""
    OUSettingDefault.objects.create(org=ou.org, setting=ou_setting, value=10)

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    assert OUSetting.objects.count() == 1
    assert OUSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOUSetting.objects.count() == 0  # Did not materialize on OrgUser

    assert result == 10


def test_ou_get_setting(ou, ou_setting):
    """org_user_get_setting() will prioritize a direct setting on the OrgUser"""
    OUSettingDefault.objects.create(org=ou.org, setting=ou_setting, value=10)
    OrgUserOUSetting.objects.create(org_user=ou, setting=ou_setting, value=20)

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    assert OUSetting.objects.count() == 1
    assert OUSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOUSetting.objects.count() == 1
    assert OrgUserOUSetting.objects.first().value == 20  # No change

    assert result == 20


def test_ou_owner(org, ou, ou_setting):
    """org_user_get_setting() where the OrgUser is the owner always pulls from OUSetting.owner_value."""
    org.owner = ou.user
    org.full_clean()
    org.save()

    OUSettingDefault.objects.create(org=ou.org, setting=ou_setting, value=10)
    OrgUserOUSetting.objects.create(org_user=ou, setting=ou_setting, value=20)

    result = services.org_user_get_setting(org_user=ou, slug="for-test")
    assert OUSetting.objects.count() == 1
    assert OUSetting.objects.first().default == 5  # No change
    assert OUSettingDefault.objects.count() == 1
    assert OUSettingDefault.objects.first().value == 10  # No change
    assert OrgUserOUSetting.objects.count() == 1
    assert OrgUserOUSetting.objects.first().value == 20  # No change

    assert result == 100
