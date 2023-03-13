import logging
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django_extensions.db.fields import AutoSlugField

import base.constants


logger = logging.getLogger(__name__)


class Org(models.Model):
    """Organizations users can belong to. They must belong to at least one."""

    slug = AutoSlugField(
        max_length=127,
        blank=True,
        editable=True,
        populate_from="name",
        unique=True,
        help_text="The name in all lowercase, suitable for URL identification",
    )
    name = models.CharField(max_length=254, help_text="The name of the organization")
    is_active = models.BooleanField(default=True)
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="orgs",
        related_query_name="orgs",
        through="OrgUser",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "slug")

    def __str__(self):
        return self.name

    def clean(self):
        if self._state.adding is False:

            # The only time a blank slug is allowed is if it's a brand new Org,
            # because AutoSlugField only triggers when saved.
            if not self.slug:
                raise ValidationError({"slug": "Slug may not be blank."})


class OrgUser(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="org_users", on_delete=models.CASCADE
    )
    org = models.ForeignKey(Org, related_name="org_users", on_delete=models.CASCADE)

    # Refer to base.constants.OrgUser.Role
    # We don't set it as a 'choice' field because we don't want to generate
    # unnecessary migrations.
    role = models.CharField(max_length=127)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "org"], name="unique_user_org")
        ]

    def clean(self):

        # If this OU isn't an owner, there must be an owner for the Org.
        if self.role != base.constants.OrgUser.Role.OWNER:
            if not self.org.org_users.filter(
                role=base.constants.OrgUser.Role.OWNER
            ).exists():
                raise ValidationError("Organization must have an owner.")
