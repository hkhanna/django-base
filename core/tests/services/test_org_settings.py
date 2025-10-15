"""Tests related to settings for Orgs, OrgUsers, and Plans."""

import pytest
from datetime import timedelta
from django.test import override_settings
from freezegun import freeze_time
from ...models import (
    OrgSetting,
    OrgUserSetting,
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


@override_settings(
    ORG_SETTING_DEFAULTS={
        "custom_feature": {"type": "bool", "default": "true"},
        "max_items": {"type": "int", "default": "100"},
    }
)
def test_org_get_setting_from_defaults(org):
    """org_get_setting() will use ORG_SETTING_DEFAULTS when a setting doesn't exist"""
    assert OrgSetting.objects.count() == 0  # No OrgSettings yet.

    # Test boolean setting from defaults
    result = services.org_get_setting_value(org=org, slug="custom_feature")
    settings = OrgSetting.objects.filter(slug="custom_feature")
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "custom_feature"
    assert setting.default == "true"
    assert setting.type == "bool"
    assert result is True

    # Test integer setting from defaults
    result = services.org_get_setting_value(org=org, slug="max_items")
    settings = OrgSetting.objects.filter(slug="max_items")
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "max_items"
    assert setting.default == "100"
    assert setting.type == "int"
    assert result == 100

    # Test fallback to hardcoded default when not in ORG_SETTING_DEFAULTS
    result = services.org_get_setting_value(org=org, slug="unknown_setting")
    settings = OrgSetting.objects.filter(slug="unknown_setting")
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "unknown_setting"
    assert setting.default == "false"
    assert setting.type == constants.SettingType.BOOL
    assert result is False


@override_settings(
    ORG_USER_SETTING_DEFAULTS={
        "can_export": {
            "type": "bool",
            "default": "false",
            "owner_value": "true",
        },
        "max_exports": {
            "type": "int",
            "default": "10",
            "owner_value": "100",
        },
    }
)
def test_org_user_get_setting_from_defaults(org):
    """org_user_get_setting_value() will use ORG_USER_SETTING_DEFAULTS when a setting doesn't exist"""
    # Create a new user for testing (not the org owner)
    new_user = services.user_create(email="testuser@example.com", password="testpass")
    org_user = services.org_user_create(org=org, user=new_user)
    assert OrgUserSetting.objects.count() == 0  # No OrgUserSettings yet.

    # Test boolean setting from defaults
    result = services.org_user_get_setting_value(org_user=org_user, slug="can_export")
    settings = OrgUserSetting.objects.filter(slug="can_export")
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "can_export"
    assert setting.default == "false"
    assert setting.owner_value == "true"
    assert setting.type == "bool"
    assert result is False  # User is not the owner

    # Test integer setting from defaults
    result = services.org_user_get_setting_value(
        org_user=org_user, slug="max_exports"
    )
    settings = OrgUserSetting.objects.filter(slug="max_exports")
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "max_exports"
    assert setting.default == "10"
    assert setting.owner_value == "100"
    assert setting.type == "int"
    assert result == 10  # User is not the owner

    # Test owner_value for org owner (owner's OrgUser already exists from org creation)
    from core import selectors

    owner_org_user = selectors.org_user_list(org=org, user=org.owner).get()
    result = services.org_user_get_setting_value(
        org_user=owner_org_user, slug="can_export"
    )
    assert result is True  # Owner gets owner_value

    result = services.org_user_get_setting_value(
        org_user=owner_org_user, slug="max_exports"
    )
    assert result == 100  # Owner gets owner_value

    # Test fallback to hardcoded default when not in ORG_USER_SETTING_DEFAULTS
    result = services.org_user_get_setting_value(
        org_user=org_user, slug="unknown_setting"
    )
    settings = OrgUserSetting.objects.filter(slug="unknown_setting")
    assert len(settings) == 1
    setting = settings.first()
    assert setting.slug == "unknown_setting"
    assert setting.default == "false"
    assert setting.owner_value == "true"
    assert setting.type == constants.SettingType.BOOL
    assert result is False
