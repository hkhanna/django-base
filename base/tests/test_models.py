from pytest_django.asserts import assertRaisesMessage
from django.apps import apps
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .. import services, selectors, models, factories

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
                snake_name = model._meta.verbose_name.replace(" ", "_").lower()
                assert hasattr(services, f"{snake_name}_create")


def test_exists_model_update():
    """Ensure a <model>_update function exists for every model."""
    for app in apps.get_app_configs():
        for model in app.get_models():
            if models.BaseModel in model.__mro__:
                snake_name = model._meta.verbose_name.replace(" ", "_").lower()
                assert hasattr(services, f"{snake_name}_update")


def test_exists_model_list():
    """Ensure a <model>_list function exists for every model."""
    for app in apps.get_app_configs():
        for model in app.get_models():
            if models.BaseModel in model.__mro__:
                snake_name = model._meta.verbose_name.replace(" ", "_").lower()
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
    user = User.objects.create(
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
