import logging
import secrets
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django_extensions.db.fields import AutoSlugField

from core import constants, utils, fields

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


class BaseManager(models.Manager):
    """Base manager for all models"""

    def get_by_natural_key(self, uuid):
        """For deserialization during django-admin loaddata."""
        return self.get(uuid=uuid)


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

    objects = BaseManager()

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        # This is set to true by the services to enforce use of services to save models.
        self._allow_save = False

        return super().__init__(*args, **kwargs)

    def natural_key(self):
        """For serialization when using django-admin dumpdata."""
        return (self.uuid,)

    def save(self, *args, **kwargs):
        """Enforce use of services to save models."""

        if self._allow_save is False:
            raise RuntimeError(
                f"Must use services to save {self._meta.model_name} models."
            )
        else:
            self._allow_save = False
            return super().save(*args, **kwargs)


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
        "core.Org",
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
    template_context = models.JSONField(default=dict, blank=True)
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
        max_length=254, choices=Status.choices, default=Status.NEW  # type: ignore
    )
    error_message = models.TextField(blank=True)

    def __str__(self):
        # This will return something like 'reset-password' since its the last part of the template prefix
        template_prefix = self.template_prefix.split("/")[-1]
        return f"{template_prefix} ({self.uuid})"


class EmailMessageAttachment(BaseModel):
    """File attachments for EmailMessages"""

    email_message = models.ForeignKey(
        EmailMessage, on_delete=models.CASCADE, related_name="attachments"
    )

    # Files are stored with the uuid.ext as the filename on S3 to avoid
    # collisions. We also store the original filename to allow us to
    # reproduce it when necessary.
    file = models.FileField(upload_to="email_message_attachments/")
    filename = models.CharField(max_length=254)
    mimetype = models.CharField(max_length=254)

    class Meta:
        order_with_respect_to = "email_message"

    def __str__(self):
        return f"{self.email_message} / {self.filename} ({self.uuid})"


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
        max_length=127, choices=Status.choices, default=Status.NEW  # type: ignore
    )

    def __str__(self):
        if self.type:
            return f"{self.type} ({self.id})"
        else:
            return f"unknown ({self.id})"


class Event(BaseModel):
    """A discrete event that occurs with respect to one or more other models in the system."""

    occurred_at = models.DateTimeField()
    type = models.CharField(max_length=127)
    data = models.JSONField(
        default=dict,
        blank=True,
    )

    def __str__(self):
        return f"{self.type} - {self.uuid}"


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
    # If we implement multi-tenant architecture, we would want to make domain
    # it's own model (OrgDomain) to avoid the risk that two orgs on the same domain are on different tenants.
    domain = models.CharField(
        max_length=254, help_text="The domain used to access the org on the web."
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_orgs"
    )
    is_active = models.BooleanField(default=True)
    primary_plan = models.ForeignKey(
        "core.Plan", on_delete=models.PROTECT, related_name="primary_orgs"
    )
    default_plan = models.ForeignKey(
        "core.Plan",
        on_delete=models.PROTECT,
        related_name="default_orgs",
        help_text="Default plan if the primary plan expires.",
    )
    current_period_end = models.DateTimeField(null=True, blank=True)
    users = models.ManyToManyField(  # type: ignore
        settings.AUTH_USER_MODEL,
        related_name="orgs",
        related_query_name="orgs",
        through="OrgUser",
    )

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
        help_text="Used by an org when no plan is specified. Only one plan can be default, so setting this will unset any other default plan.",
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


class UserManager(BaseManager):
    """Customized user manager"""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError("User must have an email address")
        email = email.lower()
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

    def get_by_natural_key(self, username):
        # We can't use UUIDs as a natural key for users unless we override
        # the default authentication backend.
        return self.get(email=username)


class User(AbstractUser):
    """Customized User model"""

    # We don't inherit from BaseModel or enforce the _allow_save checks
    # because too many built-in views mutate user instances directly.

    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="UUID",
        help_text="Secondary ID",
    )
    username = None  # type: ignore
    email = fields.EmailFieldCaseInsensitive(
        unique=True,  # Even though we have the constraint below, this is required because it is the USERNAME_FIELD.
        verbose_name="email address",
    )
    email_history = ArrayField(
        models.EmailField(),
        default=list,
        blank=True,
        help_text="Record of all email addresses the user has had.",
    )

    display_name = models.CharField(
        max_length=254,
        blank=True,
        help_text="The name that will be displayed by default to other users.",
    )
    date_joined = None  # type: ignore
    created_at = models.DateTimeField(db_index=True, default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list = []  # type: ignore

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_email_case_insensitive",
            )
        ]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<User: {self.email} (#{self.id})>"

    @property
    def name(self):
        if self.display_name:
            return self.display_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email

    def clean(self):
        # We don't want to call the parent class's clean() because
        # it will try to call a normalize_email function on the manager
        # but we don't need that because we normalize the email address as
        # part of the field.
        pass

    def natural_key(self):
        # We can't use UUIDs as a natural key for users unless we override
        # the default authentication backend.
        return (self.email,)


# -- SETTINGS: GLOBAL, ORG, ORGUSERS -- #


def check_setting_type(
    value: str, value_name: str, setting_type: constants.SettingType
) -> None:
    try:
        utils.cast_setting(value, setting_type)
    except ValueError:
        if setting_type == constants.SettingType.BOOL:
            raise ValidationError(
                f"Boolean setting must have a {value_name} of true or false."
            )
        elif setting_type == constants.SettingType.INT:
            raise ValidationError(
                f"Integer setting must have a {value_name} that is an integer."
            )
        else:
            raise


class OrgSetting(BaseModel):
    """An Org-wide setting definition"""

    slug = models.SlugField(max_length=254, unique=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)  # type: ignore
    default = models.CharField(max_length=254)

    def __str__(self):
        return f"OrgSetting: {self.slug} ({self.pk})"

    def clean(self):
        check_setting_type(self.default, "default", self.type)


class OrgUserSetting(BaseModel):
    """Definitions for settings for members of an Org, i.e., OrgUsers"""

    slug = models.SlugField(max_length=254, unique=True)
    type = models.CharField(max_length=127, choices=constants.SettingType.choices)  # type: ignore
    default = models.CharField(max_length=254)
    owner_value = models.CharField(
        max_length=254,
        help_text="The value that will be enforced for the org owner over all other defaults and values.",
    )

    def clean(self):
        check_setting_type(self.default, "default", self.type)
        check_setting_type(self.owner_value, "owner_value", self.type)

    def __str__(self):
        return f"OrgUserSetting: {self.slug} ({self.pk})"


class GlobalSetting(BaseModel):
    """A setting that applies to the entire system."""

    slug = models.SlugField(max_length=254, unique=True)
    type = models.CharField(
        max_length=127,
        choices=constants.SettingType.choices,  # type: ignore
    )
    value = models.CharField(max_length=254)

    def __str__(self):
        return f"GlobalSetting: {self.slug} ({self.pk})"

    def clean(self):
        check_setting_type(self.value, "value", self.type)


class PlanOrgSetting(BaseModel):
    """The Org-wide settings for a particular Plan. Billing-related limitations go here."""

    plan = models.ForeignKey(
        "core.Plan", on_delete=models.CASCADE, related_name="plan_org_settings"
    )
    setting = models.ForeignKey(
        "core.OrgSetting", on_delete=models.CASCADE, related_name="plan_org_settings"
    )
    value = models.CharField(max_length=254)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "setting"], name="unique_plan_setting"
            )
        ]

    def __str__(self):
        return f"PlanOrgSetting: {self.plan.slug} / {self.setting.slug} ({self.pk})"

    def clean(self):
        check_setting_type(self.value, "value", self.setting.type)


class OverriddenOrgSetting(BaseModel):
    """Used if a particular Org should override the Plan Org-wide settings."""

    # Useful if there's a custom plan for a customer or if there's only one Plan but customers
    # can make one-time purchases potentially unlocking certain settings.
    org = models.ForeignKey(
        "core.Org", on_delete=models.CASCADE, related_name="overridden_org_settings"
    )
    setting = models.ForeignKey(
        "core.OrgSetting",
        on_delete=models.CASCADE,
        related_name="overridden_org_settings",
    )
    value = models.CharField(max_length=254)

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
        check_setting_type(self.value, "value", self.setting.type)


class OrgUserOrgUserSetting(BaseModel):
    """The specific mapping of an OrgUser to an OrgUserSetting."""

    org_user = models.ForeignKey(
        "core.OrgUser",
        on_delete=models.CASCADE,
        related_name="org_user_org_user_settings",
    )
    setting = models.ForeignKey(
        "core.OrgUserSetting",
        on_delete=models.CASCADE,
        related_name="org_user_org_user_settings",
    )
    value = models.CharField(max_length=254)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["org_user", "setting"], name="unique_org_user_org_user_setting"
            )
        ]

    def __str__(self):
        return (
            f"OrgUserOrgUserSetting: {self.org_user} / {self.setting.slug} ({self.pk})"
        )

    def clean(self):
        check_setting_type(self.value, "value", self.setting.type)


class OrgUserSettingDefault(BaseModel):
    """An Org can set defaults for its OrgUsers that have not specifically set certain settings."""

    org = models.ForeignKey(
        "core.Org", on_delete=models.CASCADE, related_name="org_user_setting_defaults"
    )
    setting = models.ForeignKey(
        "core.OrgUserSetting",
        on_delete=models.CASCADE,
        related_name="org_user_setting_defaults",
    )
    value = models.CharField(max_length=254)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["org", "setting"], name="unique_org_user_setting_defaults"
            )
        ]

    def __str__(self):
        return (
            f"OrgUserSettingDefault: {self.org.slug} / {self.setting.slug} ({self.pk})"
        )

    def clean(self):
        check_setting_type(self.value, "value", self.setting.type)
