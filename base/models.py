import logging
import secrets
import uuid

from allauth.account import models as auth_models
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField

from base import constants

logger = logging.getLogger(__name__)


class UniqueConstraintNoValidation(models.UniqueConstraint):
    """Allows us to skip application-level validation of unique constraints.
    This is useful if we only want to enforce it at the database level because
    we fix the data during saving of the model.

    See. e.g., how Plan defaults are handled in services.plan_create or
    services.plan_update.
    """

    def validate(self, *args, **kwargs):
        pass


class BaseModel(models.Model):
    """Base model for all models"""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        help_text="Secondary ID",
    )
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EmailMessage(BaseModel):
    """Keep a record of every email sent in the DB."""

    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        help_text="User that caused the EmailMessage to be created.",
        null=True,
        blank=True,
    )
    org = models.ForeignKey(
        "base.Org",
        on_delete=models.SET_NULL,
        help_text="The active Org of the User that caused the EmailMessage to be created.",
        null=True,
        blank=True,
    )
    sender_name = models.CharField(max_length=254, blank=True)
    sender_email = models.EmailField()
    to_name = models.CharField(max_length=254, blank=True)
    to_email = models.EmailField()
    reply_to_name = models.CharField(max_length=254, blank=True)
    reply_to_email = models.EmailField(blank=True)
    subject = models.CharField(max_length=254, blank=True)
    template_prefix = models.CharField(max_length=254)
    template_context = models.JSONField(blank=True)
    message_id = models.CharField(
        max_length=254,
        unique=True,
        null=True,
        blank=True,
        default=None,
        help_text="Message-ID provided by the sending service as per RFC 5322",
    )
    postmark_message_stream = models.CharField(
        max_length=254, blank=True, help_text="Leave blank if not using Postmark"
    )

    Status = constants.EmailMessage.Status
    status = models.CharField(
        max_length=254, choices=Status.choices, default=Status.NEW
    )
    error_message = models.TextField(blank=True)

    def __str__(self):
        # This will return something like 'reset-password' since its the last part of the template prefix
        template_prefix = self.template_prefix.split("/")[-1]
        return f"{template_prefix} - {self.to_email}"


class EmailMessageWebhook(BaseModel):
    """Webhooks related to an outgoing EmailMessage, like bounces, spam complaints, etc."""

    received_at = models.DateTimeField(auto_now_add=True)
    body = models.JSONField()
    headers = models.JSONField()

    type = models.CharField(max_length=254, blank=True)
    email_message = models.ForeignKey(
        EmailMessage, null=True, blank=True, on_delete=models.SET_NULL
    )
    note = models.TextField(blank=True)

    Status = constants.EmailMessageWebhook.Status
    status = models.CharField(
        max_length=127, choices=Status.choices, default=Status.NEW
    )

    def __str__(self):
        if self.type:
            return f"{self.type} ({self.id})"


class Event(BaseModel):
    """A discrete event that occurs with respect to one or more other models in the system."""

    occurred_at = models.DateTimeField()
    type = models.CharField(max_length=127)
    data = models.JSONField(
        default=dict,
        blank=True,
    )

    def __str__(self):
        return f"{self.type} ({self.occurred_at})"


class Org(BaseModel):
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

    def clean(self):
        if self._state.adding is False:
            # The only time a blank slug is allowed is if it's a brand new Org,
            # because AutoSlugField only triggers when saved.
            if not self.slug:
                raise ValidationError({"slug": "Slug may not be blank."})


class OrgUser(BaseModel):
    """The 'membership' model for a User/Org relationship."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="org_users", on_delete=models.CASCADE
    )
    org = models.ForeignKey(Org, related_name="org_users", on_delete=models.CASCADE)
    last_accessed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "org"], name="unique_user_org")
        ]

    def __str__(self):
        return f"{self.org} / {self.user} ({self.pk})"


class OrgInvitation(BaseModel):
    """An invitation to join an Org"""

    org = models.ForeignKey(Org, on_delete=models.CASCADE, related_name="invitations")
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
    email_messages = models.ManyToManyField(
        "base.EmailMessage",
        related_name="org_invitations",
    )

    @property
    def status(self):
        if not self.email_messages.exists():
            return "New"
        return "Sent"


class Plan(BaseModel):
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

    class Meta:
        constraints = [
            UniqueConstraintNoValidation(
                fields=["is_default"],
                condition=models.Q(is_default=True),
                name="unique_default_plan",
            )
        ]

    def __str__(self):
        return self.slug


class OrgSetting(BaseModel):
    """An Org-wide setting"""

    slug = models.SlugField(max_length=254, unique=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)
    default = models.IntegerField()

    def __str__(self):
        return f"OrgSetting: {self.slug} ({self.pk})"

    def clean(self):
        if self.type == constants.SettingType.BOOL and self.default not in (0, 1):
            raise ValidationError("Boolean OrgSetting must have a default of 0 or 1.")


class PlanOrgSetting(BaseModel):
    """The Org-wide settings for a particular Plan. Billing-related limitations go here."""

    plan = models.ForeignKey(
        "base.Plan", on_delete=models.CASCADE, related_name="plan_org_settings"
    )
    setting = models.ForeignKey(
        "base.OrgSetting", on_delete=models.CASCADE, related_name="plan_org_settings"
    )
    value = models.IntegerField()

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


class OverriddenOrgSetting(BaseModel):
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


class OrgUserSetting(BaseModel):
    """Settings for members of an Org, i.e., OrgUsers"""

    slug = models.SlugField(max_length=254, unique=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)
    default = models.IntegerField()
    owner_value = models.IntegerField(
        help_text="The value that will be enforced for the org owner over all other defaults and values."
    )

    def clean(self):
        if self.type == constants.SettingType.BOOL and (
            self.default not in (0, 1) or self.owner_value not in (0, 1)
        ):
            raise ValidationError(
                "Boolean OrgUserSetting must have a default and owner_value of 0 or 1."
            )

    def __str__(self):
        return f"OrgUserSetting: {self.slug} ({self.pk})"


class OrgUserOUSetting(BaseModel):
    """The specific mapping of an OrgUser to an OrgUserSetting."""

    org_user = models.ForeignKey(
        "base.OrgUser",
        on_delete=models.CASCADE,
        related_name="org_user_ou_settings",
    )
    setting = models.ForeignKey(
        "base.OrgUserSetting",
        on_delete=models.CASCADE,
        related_name="org_user_ou_settings",
    )
    value = models.IntegerField()

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


class OUSettingDefault(BaseModel):
    """An Org can set defaults for its OrgUsers that have not specifically set certain settings."""

    org = models.ForeignKey(
        "base.Org", on_delete=models.CASCADE, related_name="ou_setting_defaults"
    )
    setting = models.ForeignKey(
        "base.OrgUserSetting",
        on_delete=models.CASCADE,
        related_name="ou_setting_defaults",
    )
    value = models.IntegerField()

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


class UserManager(BaseUserManager):
    """Customized user manager"""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError("User must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Customized User model"""

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        help_text="Secondary ID",
    )
    username = None  # type: ignore
    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={"unique": "A user with that email already exists."},
    )
    is_locked = models.BooleanField(
        "locked", default=False, help_text="Prevent the user from logging in."
    )
    email_history = ArrayField(
        models.EmailField(),
        default=list,
        blank=True,
        help_text="Record of all email addresses the user has had.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<User: {self.email} (#{self.id})>"

    def save(self, *args, **kwargs):
        # Normalize all emails to lowercase. This is mostly for emails saved via the admin since
        # we already normalize in the settings/signup forms.
        self.email = self.email.lower()

        # Keep a record of all email addresses
        if len(self.email_history) == 0:
            self.email_history.append(self.email)
        elif self.email_history[-1] != self.email:
            self.email_history.append(self.email)

        adding = False
        if self._state.adding is True:
            # If we don't set this now, self._state.adding doesn't work
            # properly once we have saved the user.
            adding = True

        super().save(*args, **kwargs)

        # Auto-create a personal org if the user doesn't have any active orgs.
        from base import services

        if not self.orgs.filter(is_active=True).exists():
            Plan = apps.get_model("base", "Plan")
            default_plan, _ = Plan.objects.get_or_create(
                is_default=True, defaults={"name": "Default"}
            )
            services.org_create(
                owner=self,
                is_personal=True,
                name=self.name,
                is_active=True,
                primary_plan=default_plan,
                default_plan=default_plan,
            )

        if not adding:
            # Conform the name of the personal org if the user has one.
            if org := self.personal_org:
                services.org_update(instance=org, name=self.name)

    def clean(self):
        # Case-insensitive email address uniqueness check
        if User.objects.filter(email__iexact=self.email).exclude(id=self.id).exists():
            raise ValidationError({"email": "A user with that email already exists."})

        if self.is_locked and not self.is_active:
            raise ValidationError(
                {
                    "is_locked": "A locked user must be active.",
                    "is_active": "A locked user must be active.",
                }
            )

        if not self._state.adding:
            # Don't require an Org for a brand new user
            if self.orgs.count() == 0:
                raise ValidationError(
                    "A user must belong to at least one organization."
                )

    def sync_changed_email(self):
        """If user.email has changed, remove all a User's EmailAddresses
        (although they should only have one), and replace it with the new one.
        Returns the EmailAddress if one was created to send a confirmation email if desired.
        """
        if not auth_models.EmailAddress.objects.filter(
            user=self, email__iexact=self.email
        ).exists():
            auth_models.EmailAddress.objects.filter(user=self).delete()
            email_address = auth_models.EmailAddress.objects.create(
                user=self, email=self.email, primary=True, verified=False
            )
            return email_address
        else:
            return None

    @property
    def created_at(self):
        return self.date_joined

    @property
    def is_email_verified(self):
        email_address = self.emailaddress_set.first()
        if not email_address:
            email_address = self.sync_changed_email()
        return email_address.verified

    @property
    def name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email

    @property
    def personal_org(self):
        return self.orgs.filter(owner=self, is_personal=True, is_active=True).first()

    @property
    def default_org(self):
        # Use the most recently accessed org.
        ou = (
            self.org_users.filter(org__is_active=True)
            .order_by("-last_accessed_at")
            .first()
        )

        assert ou is not None, "User does not have any Orgs"
        return ou.org
