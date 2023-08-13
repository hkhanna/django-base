from typing import TypeVar

from django.db import models

from .models import (
    User as UserType,
)  # mypy: Can't use get_user_model because of https://github.com/typeddjango/django-stubs/issues/599

from .models import BaseModel

# Generic type for a Django model
# Reference: https://mypy.readthedocs.io/en/stable/kinds_of_types.html#the-type-of-class-objects
ModelType = TypeVar("ModelType", bound=models.Model)

# Generic type for our custom Django base model
BaseModelType = TypeVar("BaseModelType", bound=BaseModel)
