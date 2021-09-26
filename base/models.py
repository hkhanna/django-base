import logging
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager

from . import tasks

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

    username = None
    email = models.EmailField(
        "email address",
        unique=True,
        error_messages={"unique": "A user with that email already exists."},
    )
    is_locked = models.BooleanField(
        "locked", default=False, help_text="Prevent the user from logging in."
    )
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

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

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<User: {self.email} (#{self.id})>"


class EmailMessage(models.Model):
    """Keep a record of every email sent in the DB."""

    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="User that caused the EmailMessage to be created.",
    )
    sender = models.CharField(max_length=254, blank=True)
    to_name = models.CharField(max_length=254, blank=True)
    to_email = models.EmailField()
    subject = models.CharField(max_length=254, blank=True)
    template_prefix = models.CharField(max_length=254)
    template_context = models.JSONField()
    postmark_message_stream = models.CharField(
        max_length=254, blank=True, help_text="Leave blank if not using Postmark"
    )

    class Status(models.TextChoices):
        NEW = "new"
        READY = "ready"
        PENDING = "pending"
        SENT = "sent"
        CANCELED = "canceled"
        ERROR = "error"

    status = models.CharField(
        max_length=254, choices=Status.choices, default=Status.NEW
    )
    error_message = models.TextField(blank=True)

    @staticmethod
    def _sanitize_string(field):
        """Remove superfluous linebreaks and whitespace"""
        lines = field.splitlines()
        sanitized_lines = []
        for line in lines:
            sanitized_line = line.strip()
            if sanitized_line:  # Remove blank lines
                sanitized_lines.append(line.strip())
        sanitized = " ".join(sanitized_lines).strip()
        return sanitized

    def cooling_down(self, period, allowed):
        """Check that this created_by/template_prefix/to_email combination hasn't been recently sent."""
        cooldown_period = timedelta(seconds=period)
        return (
            EmailMessage.objects.filter(
                sent_at__gt=timezone.now() - cooldown_period,
                created_by=self.created_by,
                template_prefix=self.template_prefix,
                to_email=self.to_email,
            ).count()
            >= allowed
        )

    def send(self, attachments=[], cooldown_period=180, cooldown_allowed=1):
        if self.status != EmailMessage.Status.NEW:
            raise RuntimeError(
                f"EmailMessage.id={self.id} EmailMessage.send() called on an email that is not status=NEW"
            )
        self.prepare()

        if self.cooling_down(cooldown_period, cooldown_allowed):
            self.status = EmailMessage.Status.CANCELED
            self.save()
            return False
        else:
            tasks.send_email_message(self.id, attachments)
            return True

    def prepare(self):
        """Updates the context with defaults and other sanity checking"""
        if not self.sender:
            self.sender = settings.SITE_CONFIG["default_from_email"]
        self.sender = self._sanitize_string(self.sender)
        self.to_name = self._sanitize_string(self.to_name)
        self.to_email = self._sanitize_string(self.to_email)

        default_context = {
            "logo_url": settings.SITE_CONFIG["logo_url"],
            "logo_url_link": settings.SITE_CONFIG["logo_url_link"],
            "contact_email": settings.SITE_CONFIG["contact_email"],
            "site_name": settings.SITE_CONFIG["name"],
            "company": settings.SITE_CONFIG["company"],
            "company_address": settings.SITE_CONFIG["company_address"],
            "company_city_state_zip": settings.SITE_CONFIG["company_city_state_zip"],
        }
        for k, v in default_context.items():
            if k not in self.template_context:
                self.template_context[k] = v

        # Render subject from template if not already set
        if not self.subject:
            self.subject = render_to_string(
                "{0}_subject.txt".format(self.template_prefix), self.template_context
            )
        self.subject = self._sanitize_string(self.subject)
        if len(self.subject) > settings.MAX_SUBJECT_LENGTH:
            self.subject = self.subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
        self.template_context["subject"] = self.subject

        self.status = EmailMessage.Status.READY
        self.save()

    def __str__(self):
        # This will return something like 'reset-password' since its the last part of the template prefix
        return self.template_prefix.split("/")[-1]
