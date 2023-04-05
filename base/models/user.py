import logging
import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import AbstractUser, BaseUserManager
from allauth.account import models as auth_models

logger = logging.getLogger(__name__)


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
    username = None
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
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

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

        # Auto-create a personal org if the user doesn't have any orgs.
        if not self.orgs.exists():
            Org = apps.get_model("base", "Org")
            Plan = apps.get_model("base", "Plan")
            default_plan, _ = Plan.objects.get_or_create(
                is_default=True, defaults={"name": "Default"}
            )
            Org.objects.get_or_create(
                owner=self,
                is_personal=True,
                defaults={
                    "name": self.name,
                    "is_active": True,
                    "primary_plan": default_plan,
                    "default_plan": default_plan,
                },
            )

        if not adding:
            # Conform the name of the personal org if the user has one.
            org = self.personal_org
            if org:
                org.name = self.name
                org.full_clean()
                org.save()

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
        Returns the EmailAddress if one was created to send a confirmation email if desired."""
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
