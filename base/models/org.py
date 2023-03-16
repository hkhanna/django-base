import logging
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django_extensions.db.fields import AutoSlugField
from django.utils.encoding import force_str
from django.utils import timezone

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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_orgs"
    )
    is_personal = models.BooleanField()
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
        constraints = [
            models.UniqueConstraint(
                fields=["owner"],
                condition=models.Q(is_personal=True, is_active=True),
                name="unique_personal_active_org",
            )
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # If this is a personal org, update the slug.
        if self.is_personal:
            self.slug = force_str(Org._meta.get_field("slug").create_slug(self, True))

        super().save(*args, **kwargs)

        # If owner isn't an OrgUser, create one.
        OrgUser.objects.update_or_create(
            user=self.owner,
            org=self,
            defaults={"role": settings.DEFAULT_ORG_OWNER_ROLE},
        )

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
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(default=timezone.now)

    # Recommend defining constants somewhere.  We don't set it as a 'choice' field
    # because we don't want to generate unnecessary migrations.
    role = models.CharField(max_length=127)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "org"], name="unique_user_org")
        ]
