"""Tests related to settings for Orgs, OrgUsers, and Plans."""
import pytest
from datetime import timedelta
from freezegun import freeze_time
from ...models import (
    OrgSetting,
    PlanOrgSetting,
    OverriddenOrgSetting,
)
from core import constants, services


@pytest.fixture
def org_setting():
    return services.org_setting_create(
        slug="for-test", default="5", type=constants.SettingType.INT
    )


def test_org_get_setting_noexist(org):
    """org_get_setting() will create an OrgSetting with a default of False if it is accessed but does not exist"""
    assert OrgSetting.objects.count() == 0  # No OrgSettings yet.

    result = services.org_get_setting_value(org=org, slug="for-test")
    settings = OrgSetting.objects.all()
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "for-test"
    assert setting.default == "false"
    assert setting.type == constants.SettingType.BOOL
    assert result is False


def test_org_get_setting_noplan(org, org_setting):
    """org_get_setting() will materialize an OrgSetting on the Plan if it isn't already on the Plan"""
    result = services.org_get_setting_value(org=org, slug="for-test")
    assert OrgSetting.objects.count() == 1
    # Setting shouldn't change
    assert org_setting.slug == "for-test"
    assert org_setting.default == "5"
    assert org_setting.type == constants.SettingType.INT
    assert result == 5

    # Materialized on Plan
    assert org.primary_plan.plan_org_settings.first().setting == org_setting


def test_org_get_setting_plan(org, org_setting):
    """org_get_setting() in the normal case will retrieve the OrgSetting from the Plan"""
    services.plan_org_setting_create(
        plan=org.primary_plan, setting=org_setting, value="10"
    )

    result = services.org_get_setting_value(org=org, slug="for-test")
    assert OrgSetting.objects.count() == 1
    assert OrgSetting.objects.first().default == "5"  # No change
    assert PlanOrgSetting.objects.count() == 1
    assert PlanOrgSetting.objects.first().value == "10"  # No change
    assert result == 10


def test_org_get_setting_override(org, org_setting):
    """org_get_setting() will prioritize any OverriddenOrgSettings"""
    services.plan_org_setting_create(
        plan=org.primary_plan, setting=org_setting, value="10"
    )
    services.overridden_org_setting_create(org=org, setting=org_setting, value="20")

    result = services.org_get_setting_value(org=org, slug="for-test")
    assert OrgSetting.objects.count() == 1
    assert OrgSetting.objects.first().default == "5"  # No change
    assert PlanOrgSetting.objects.count() == 1
    assert PlanOrgSetting.objects.first().value == "10"  # No change
    assert OverriddenOrgSetting.objects.count() == 1
    assert OverriddenOrgSetting.objects.first().value == "20"  # No change
    assert result == 20


def test_org_get_setting_plan_expired(org, org_setting):
    """If Org.current_period_end is expired, org_get_setting() should look to Org.default_plan"""
    services.plan_org_setting_create(
        plan=org.primary_plan, setting=org_setting, value="10"
    )
    with freeze_time(org.current_period_end + timedelta(seconds=1)):
        result = services.org_get_setting_value(org=org, slug="for-test")
        assert OrgSetting.objects.count() == 1
        assert OrgSetting.objects.first().default == "5"  # No change
        assert (
            PlanOrgSetting.objects.count() == 2
        )  # A setting was created on the default_plan
        assert result == 5  # Uses the default

        default_setting = org.default_plan.plan_org_settings.first()
        services.plan_org_setting_update(instance=default_setting, value="30")
        result = services.org_get_setting_value(org=org, slug="for-test")
        assert result == 30  # Use the specified

    result = services.org_get_setting_value(org=org, slug="for-test")
    assert result == 10  # Use the primary plan's now that we're not expired.


def test_org_get_setting_plan_never_expires(org, org_setting):
    """If Org.current_period_end is None, the plan never expires."""
    services.plan_org_setting_create(
        plan=org.primary_plan, setting=org_setting, value="10"
    )
    services.org_update(instance=org, current_period_end=None)
    result = services.org_get_setting_value(org=org, slug="for-test")
    assert result == 10
