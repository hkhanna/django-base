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


def test_one_org(user):
    """A user must belong to at least one Org."""
    user.orgs.clear()
    with assertRaisesMessage(
        ValidationError, "A user must belong to at least one organization."
    ):
        user.full_clean()


def test_auto_create_org():
    """Creating a user creates their personal organization"""
    assert models.Org.objects.count() == 0
    user = services.user_create(
        first_name="First", last_name="Last", email="first@example.com"
    )

    assert models.Org.objects.count() == 1
    org = models.Org.objects.first()
    assert org.owner == user
    assert org.is_personal is True
    assert org.is_active is True
    assert list(org.users.all()) == [user]


def test_maximum_personal(user):
    """User can have a maximum of 1 personal, active org."""
    # A user doesn't necessarily have to have a personal org.
    # Think a corporate rank-and-file employee who was invited by their company admin.
    assert models.Org.objects.filter(owner=user, is_personal=True).count() == 1

    factories.org_create(owner=user, is_personal=False, name=user.name)  # OK
    factories.org_create(
        owner=user, is_personal=True, is_active=False, name=user.name
    )  # OK

    with assertRaisesMessage(ValidationError, "unique_personal_active_org"):
        factories.org_create(owner=user, is_personal=True, name=user.name)


def test_change_user_name_org_name(user):
    """Changing a user's name should change the name of the user's personal org."""
    user.first_name = "Kipp"
    user.full_clean()
    user.save()

    assert user.personal_org.name == user.name


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
