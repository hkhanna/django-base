import logging
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django_extensions.db.fields import AutoSlugField
from django.utils.encoding import force_str
from django.utils import timezone
from base import constants

logger = logging.getLogger(__name__)


class Org(models.Model):
    """Organizations users can belong to. They must belong to at least one."""

    name = models.CharField(max_length=254, help_text="The name of the organization")
    slug = AutoSlugField(
        max_length=127,
        blank=True,
        editable=True,
        populate_from="name",
        unique=True,
        help_text="The name in all lowercase, suitable for URL identification",
    )
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_orgs"
    )
    is_personal = models.BooleanField()
    primary_plan = models.ForeignKey(
        "base.Plan", on_delete=models.PROTECT, related_name="primary_orgs"
    )
    default_plan = models.ForeignKey(
        "base.Plan",
        on_delete=models.PROTECT,
        related_name="default_orgs",
        help_text="Default plan if the primary plan expires.",
    )
    current_period_end = models.DateTimeField(null=True, blank=True)
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

    def get_plan(self):
        """Returns the primary_plan or default_plan as a function of current_period_end."""
        if self.current_period_end and timezone.now() > self.current_period_end:
            return self.default_plan
        return self.primary_plan

    def get_setting(self, slug):
        # See test_org_settings.py for an explanation of how this works.

        setting, _ = OrgSetting.objects.get_or_create(
            slug=slug, defaults={"type": constants.SettingType.BOOL, "default": 0}
        )

        overridden_org_setting = OverriddenOrgSetting.objects.filter(
            org=self, setting=setting
        ).first()

        if overridden_org_setting:
            best = overridden_org_setting.value
        else:
            plan = self.get_plan()
            plan_org_setting, _ = PlanOrgSetting.objects.get_or_create(
                plan=plan,
                setting=setting,
                defaults={"value": setting.default},
            )
            best = plan_org_setting.value

        if setting.type == constants.SettingType.BOOL:
            return bool(best)

        return best


class OrgUser(models.Model):
    """The 'membership' model for a User/Org relationship."""

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


class Plan(models.Model):
    """Represents a group of OrgSettings. Often tied to billing."""

    name = models.CharField(max_length=254, unique=True)
    slug = AutoSlugField(
        max_length=127,
        blank=True,
        overwrite=True,
        populate_from="name",
        unique=True,
        help_text="The name in all lowercase, suitable for URL identification",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class OrgSetting(models.Model):
    """An Org-wide setting"""

    slug = models.SlugField(max_length=254, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)
    default = models.IntegerField(default=0)

    def clean(self):
        if self.type == constants.SettingType.BOOL and self.default not in (0, 1):
            raise ValidationError("Boolean OrgSetting must have a default of 0 or 1.")


class PlanOrgSetting(models.Model):
    """The Org-wide settings for a particular Plan. Billing-related limitations go here."""

    plan = models.ForeignKey(
        "base.Plan", on_delete=models.CASCADE, related_name="plan_org_settings"
    )
    setting = models.ForeignKey(
        "base.OrgSetting", on_delete=models.CASCADE, related_name="plan_org_settings"
    )
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "setting"], name="unique_plan_setting"
            )
        ]

    def __str__(self):
        return self.setting.slug

    def clean(self):
        if self.setting.type == constants.SettingType.BOOL and self.value not in (0, 1):
            raise ValidationError(
                "Boolean PlanOrgSetting must have a default of 0 or 1."
            )


class OverriddenOrgSetting(models.Model):
    """Used if a particular Org should override the Plan Org-wide settings."""

    # Useful if there's a custom plan for a customer or if there's only one Plan but customers
    # can make one-time purchases potentially unlocking certain settings.
    org = models.ForeignKey(
        "base.Org", on_delete=models.CASCADE, related_name="overridden_org_settings"
    )
    setting = models.ForeignKey(
        "base.OrgSetting",
        on_delete=models.CASCADE,
        related_name="overridden_org_settings",
    )
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["org", "setting"], name="unique_overridden_org_setting"
            )
        ]

    def __str__(self):
        return self.setting.slug

    def clean(self):
        if self.setting.type == constants.SettingType.BOOL and self.value not in (0, 1):
            raise ValidationError(
                "Boolean OverriddenOrgSetting must have a default of 0 or 1."
            )


class OUSetting(models.Model):
    """Settings for members of an Org, i.e., OrgUsers"""

    slug = models.SlugField(max_length=254, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)
    default = models.IntegerField(default=0)


class OrgUserOUSetting(models.Model):
    """The specific mapping of an OrgUser to an OUSetting."""

    org_user = models.ForeignKey(
        "base.OrgUser",
        on_delete=models.CASCADE,
        related_name="org_user_ou_settings",
    )
    setting = models.ForeignKey(
        "base.OUSetting",
        on_delete=models.CASCADE,
        related_name="org_user_ou_settings",
    )
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["org_user", "setting"], name="unique_org_user_ou_setting"
            )
        ]

    def __str__(self):
        return self.setting.slug


class OUSettingDefaults(models.Model):
    """An Org can set defaults for its OrgUsers that have not specifically set certain settings."""

    org = models.ForeignKey(
        "base.Org", on_delete=models.CASCADE, related_name="ou_setting_defaults"
    )
    setting = models.ForeignKey(
        "base.OUSetting",
        on_delete=models.CASCADE,
        related_name="ou_setting_defaults",
    )
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["org", "setting"], name="unique_ou_setting_defaults"
            )
        ]

    def __str__(self):
        return self.setting.slug
