from django.apps import apps
from .. import services, selectors, models


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
