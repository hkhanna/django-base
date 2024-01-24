from importlib import import_module
from pytest_django.asserts import assertRaisesMessage
from django.apps import apps
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from . import factories
from .. import services, selectors, models, constants, utils

User = get_user_model()

# When a model inherits from BaseModel, it opts into the requirement that
# have a <model>_create, <model>_update, and <model>_list function.
# It also has the admin use those functions instead of directly saving.
# These tests makes sure those functions exist.


def test_exists_model_create():
    """Ensure a <model>_create function exists for every model."""
    for app in apps.get_app_configs():
        for model in app.get_models():
            if models.BaseModel in model.__mro__:
                services = import_module(f"{app.name}.services")
                snake_name = utils.get_snake_case(model)
                assert hasattr(services, f"{snake_name}_create")


def test_exists_model_update():
    """Ensure a <model>_update function exists for every model."""
    for app in apps.get_app_configs():
        for model in app.get_models():
            if models.BaseModel in model.__mro__:
                services = import_module(f"{app.name}.services")
                snake_name = utils.get_snake_case(model)
                assert hasattr(services, f"{snake_name}_update")


def test_exists_model_list():
    """Ensure a <model>_list function exists for every model."""
    for app in apps.get_app_configs():
        for model in app.get_models():
            if models.BaseModel in model.__mro__:
                selectors = import_module(f"{app.name}.selectors")
                snake_name = utils.get_snake_case(model)
                assert hasattr(selectors, f"{snake_name}_list")


def test_org_setting_boolean(org):
    """OrgSettings of type bool may only have a value of true or false."""
    org_setting = services.org_setting_create(
        slug="for-test", type=constants.SettingType.BOOL, default="false"
    )
    services.org_setting_update(instance=org_setting, default="true")  # OK

    with assertRaisesMessage(ValidationError, "true or false"):
        org_setting.default = "1"
        org_setting.full_clean()

    with assertRaisesMessage(ValidationError, "true or false"):
        models.PlanOrgSetting(
            plan=org.primary_plan, setting=org_setting, value="1"
        ).full_clean()

    with assertRaisesMessage(ValidationError, "true or false"):
        models.OverriddenOrgSetting(
            org=org, setting=org_setting, value="1"
        ).full_clean()


def test_org_user_setting_boolean(ou):
    """OrgUserSettings of type bool may only have a value of true or false."""
    org_user_setting = services.org_user_setting_create(
        slug="for-test",
        type=constants.SettingType.BOOL,
        default="false",
        owner_value="true",
    )

    services.org_user_setting_update(instance=org_user_setting, default="true")  # OK

    with assertRaisesMessage(ValidationError, "true or false"):
        services.org_user_setting_update(instance=org_user_setting, default="1")

    org_user_setting.refresh_from_db()

    with assertRaisesMessage(ValidationError, "true or false"):
        services.org_user_setting_update(instance=org_user_setting, owner_value="1")

    with assertRaisesMessage(ValidationError, "true or false"):
        models.OrgUserSettingDefault(
            org=ou.org, setting=org_user_setting, value="1"
        ).full_clean()

    with assertRaisesMessage(ValidationError, "true or false"):
        models.OrgUserOrgUserSetting(
            org_user=ou, setting=org_user_setting, value="1"
        ).full_clean()


def test_org_setting_int(org):
    """OrgSettings of type int may only have an integer-castable value."""
    org_setting = services.org_setting_create(
        slug="for-test", type=constants.SettingType.INT, default="5"
    )
    services.org_setting_update(instance=org_setting, default="0")  # OK

    with assertRaisesMessage(ValidationError, "that is an integer"):
        org_setting.default = "kipp"
        org_setting.full_clean()

    with assertRaisesMessage(ValidationError, "that is an integer"):
        models.PlanOrgSetting(
            plan=org.primary_plan, setting=org_setting, value="kipp"
        ).full_clean()

    with assertRaisesMessage(ValidationError, "that is an integer"):
        models.OverriddenOrgSetting(
            org=org, setting=org_setting, value="kipp"
        ).full_clean()


def test_org_user_setting_int(ou):
    """OrgUserSettings of type int may only have an integer-castable value."""
    org_user_setting = services.org_user_setting_create(
        slug="for-test",
        type=constants.SettingType.INT,
        default="5",
        owner_value="10",
    )

    services.org_user_setting_update(instance=org_user_setting, default="5")  # OK

    with assertRaisesMessage(ValidationError, "that is an integer"):
        services.org_user_setting_update(instance=org_user_setting, default="kipp")

    org_user_setting.refresh_from_db()

    with assertRaisesMessage(ValidationError, "that is an integer"):
        services.org_user_setting_update(instance=org_user_setting, owner_value="kipp")

    with assertRaisesMessage(ValidationError, "that is an integer"):
        models.OrgUserSettingDefault(
            org=ou.org, setting=org_user_setting, value="kipp"
        ).full_clean()

    with assertRaisesMessage(ValidationError, "that is an integer"):
        models.OrgUserOrgUserSetting(
            org_user=ou, setting=org_user_setting, value="kipp"
        ).full_clean()
