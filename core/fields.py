from django.db import models


class EmailFieldCaseInsensitive(models.EmailField):
    """Normalizes email case during cleaning."""

    def to_python(self, value):
        value = super().to_python(value)
        if value:
            return value.lower()
        else:
            return value
