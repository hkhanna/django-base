import logging
import uuid
import secrets
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django_extensions.db.fields import AutoSlugField
from django.utils.encoding import force_str
from django.utils import timezone
from base import constants, utils
from base.models.email import EmailMessage

logger = logging.getLogger(__name__)

User = get_user_model()


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
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_orgs"
    )
    is_active = models.BooleanField(default=True)
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
        )

    def add_user(self, user):
        """Create an OrgUser for this Org and return the OrgUser."""
        ou = OrgUser(org=self, user=user)
        ou.full_clean()
        ou.save()
        return ou

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

    def invite_email(self, email: str, user):
        oi = OrgInvitation(org=self, email=email, created_by=user)
        oi.full_clean()
        oi.save()
        oi.send()
        return oi


class OrgUser(models.Model):
    """The 'membership' model for a User/Org relationship."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="org_users", on_delete=models.CASCADE
    )
    org = models.ForeignKey(Org, related_name="org_users", on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "org"], name="unique_user_org")
        ]

    def __str__(self):
        return f"{self.org} / {self.user} ({self.pk})"

    def get_setting(self, slug):
        # See test_org_settings.py for an explanation of how this works.

        setting, _ = OUSetting.objects.get_or_create(
            slug=slug,
            defaults={
                "type": constants.SettingType.BOOL,
                "default": 0,
                "owner_value": 1,
            },
        )

        # Short-circuit if the OrgUser is the Org owner.
        if self.org.owner == self.user:
            if setting.type == constants.SettingType.BOOL:
                return bool(setting.owner_value)
            else:
                return setting.owner_value

        org_user_ou_setting = OrgUserOUSetting.objects.filter(
            org_user=self, setting=setting
        ).first()
        if org_user_ou_setting:
            best = org_user_ou_setting.value
        else:
            ou_setting_default, _ = OUSettingDefault.objects.get_or_create(
                org=self.org, setting=setting, defaults={"value": setting.default}
            )
            best = ou_setting_default.value

        if setting.type == constants.SettingType.BOOL:
            return bool(best)

        return best


class OrgInvitation(models.Model):
    """An invitation to join an Org"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(Org, on_delete=models.CASCADE)
    token = models.CharField(max_length=254, default=secrets.token_urlsafe)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="org_invitations_created",
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="org_invitations_received",
    )

    email = models.EmailField(help_text="Email address of the invitee")
    email_message = models.ForeignKey(
        "base.EmailMessage", on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):

        # If we're creating an invitation and there's an existing user, connect them.
        if self._state.adding:
            existing = User.objects.filter(email=self.email, is_active=True).first()
            if existing:
                self.invitee = existing

        super().save(*args, **kwargs)

    def send(self):
        sender_email = settings.SITE_CONFIG["default_from_email"]
        sender_name = utils.get_email_display_name(
            self.created_by,
            header="From",
            email=sender_email,
            suffix=f"via {settings.SITE_CONFIG['name']}",
        )

        reply_to_name = utils.get_email_display_name(self.created_by, header="Reply-To")
        reply_to_email = self.created_by.email

        to_name = ""
        if self.invitee:
            to_name = self.invitee.name

        self.email_message = EmailMessage(
            created_by=self.created_by,
            org=self.org,
            to_name=to_name,
            to_email=self.email,
            sender_name=sender_name,
            sender_email=sender_email,
            reply_to_name=reply_to_name,
            reply_to_email=reply_to_email,
            template_prefix="base/email/org_invitation",
            template_context={
                "org_name": self.org.name,
                "new_user": self.invitee is None,
            },
        )
        self.email_message.send()
        self.save()

    @property
    def status(self):
        if not self.email_message:
            return "New"
        return "Sent"


# -- Plans & Settings -- #


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
    is_default = models.BooleanField(
        default=False,
        help_text="Used when no plan is specified. E.g., for users' personal orgs. Only one plan can be default, so setting this will unset any other default plan.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="unique_default_plan",
            )
        ]

    def __str__(self):
        return self.slug

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # If this plan is set to the default, unset default on all other plans.
            if self.is_default:
                count = Plan.objects.exclude(pk=self.pk).update(is_default=False)
                if count:
                    logger.warning(
                        f"Unset is_default on {count} Plans. This is okay if you meant to change the default Plan."
                    )
            super().save(*args, **kwargs)


class OrgSetting(models.Model):
    """An Org-wide setting"""

    slug = models.SlugField(max_length=254, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)
    default = models.IntegerField()

    def __str__(self):
        return f"OrgSetting: {self.slug} ({self.pk})"

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
        return f"PlanOrgSetting: {self.plan.slug} / {self.setting.slug} ({self.pk})"

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
        return (
            f"OverriddenOrgSetting: {self.org.slug} / {self.setting.slug} ({self.pk})"
        )

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
    default = models.IntegerField()
    owner_value = models.IntegerField(
        help_text="The value that will be enforced for the org owner over all other defaults and values."
    )

    class Meta:
        verbose_name = "Org user setting"

    def clean(self):
        if self.type == constants.SettingType.BOOL and (
            self.default not in (0, 1) or self.owner_value not in (0, 1)
        ):
            raise ValidationError(
                "Boolean OUSetting must have a default and owner_value of 0 or 1."
            )

    def __str__(self):
        return f"OUSetting: {self.slug} ({self.pk})"


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
        verbose_name = "Org user org user setting"
        constraints = [
            models.UniqueConstraint(
                fields=["org_user", "setting"], name="unique_org_user_ou_setting"
            )
        ]

    def __str__(self):
        return f"OrgUserOUSetting: {self.org_user} / {self.setting.slug} ({self.pk})"

    def clean(self):
        if self.setting.type == constants.SettingType.BOOL and self.value not in (0, 1):
            raise ValidationError(
                "Boolean OrgUserOUSetting must have a default of 0 or 1."
            )


class OUSettingDefault(models.Model):
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
        verbose_name = "Org user setting default"
        constraints = [
            models.UniqueConstraint(
                fields=["org", "setting"], name="unique_ou_setting_defaults"
            )
        ]

    def __str__(self):
        return f"OUSettingDefault: {self.org.slug} / {self.setting.slug} ({self.pk})"

    def clean(self):
        if self.setting.type == constants.SettingType.BOOL and self.value not in (0, 1):
            raise ValidationError(
                "Boolean OUSettingDefault must have a default of 0 or 1."
            )
