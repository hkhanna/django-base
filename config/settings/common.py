"""
Django settings for project.

Generated by 'django-admin startproject' using Django 3.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os.path
from pathlib import Path
import logging.config
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()

READ_DOT_ENV_FILE = env.str("DJANGO_SETTINGS_MODULE") != "config.settings.production"
if READ_DOT_ENV_FILE and os.path.exists(BASE_DIR / ".env"):
    # OS environment variables take precedence over variables from .env
    env.read_env(str(BASE_DIR / ".env"))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS: list = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    "django.contrib.staticfiles",
    "heroicons",
    # "dbbackup",
    "django_extensions",
    "django_components",
    "django_vite",
    # Non-core apps should come before core so layouts can be overriden.
    # core must come before admin because it overrides an admin template
    # core must come before allauth so that core templates take precedence
    "core.apps.CoreConfig",
    "django.contrib.admin",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.github",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "core.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.DisableClientCacheMiddleware",
    "core.middleware.TimezoneMiddleware",
    "core.middleware.SetRemoteAddrFromForwardedFor",
    "core.middleware.BadRouteDetectMiddleware",
    "core.middleware.HostUrlconfMiddleware",
    "core.middleware.OrgMiddleware",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": ["django_components.templatetags.component_tags"],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# My Additions
# ---------------------
ENVIRONMENT = env.str("DJANGO_SETTINGS_MODULE").split(".")[-1]

# This is a good article for how to build custom users with the email as username
# inheriting from AbstractUser rather than AbstractUserBase:
# https://www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username
AUTH_USER_MODEL = "core.User"
ATOMIC_REQUESTS = False

ADMIN_URL_PATH = env("ADMIN_URL_PATH", default="admin/")

# If someday Render passes us a request id, we can use it in the request
# logging middleware.
REQUEST_ID_HEADER = None

# User media
# This is unset in production for django-storages / S3.
MEDIA_ROOT = BASE_DIR / ".media/"

# django_dbbackup
# DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
# DBBACKUP_STORAGE_OPTIONS = {"location": BASE_DIR / ".backups/"}
# DBBACKUP_GPG_RECIPIENT = "base-fedora@<domain>"

# EMAIL
# If there's a POSTMARK_API_KEY (for the Sandbox server), use the Postmark backend.
# Otherwise, output to the console.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
POSTMARK_API_KEY = env("POSTMARK_API_KEY", default=None)
POSTMARK_DEFAULT_STREAM_ID = env("POSTMARK_DEFAULT_STREAM_ID", default="outbound")
if POSTMARK_API_KEY:
    EMAIL_BACKEND = "postmark.django_backend.EmailBackend"
    POSTMARK_TEST_MODE = False
    POSTMARK_RETURN_MESSAGE_ID = True
MAX_SUBJECT_LENGTH = 78
EMAIL_MESSAGE_WEBHOOK_PATH = env(
    "EMAIL_MESSAGE_WEBHOOK_PATH", default="email_message_webhook/"
)

# Site Configuration - Refactor this if >1 Site is hosted from this codebase.
SITE_ID = 1
SITE_CONFIG = {
    "name": "Fedora Base",
    "logo_url_link": "",
    "logo_url": "",
    "default_from_name": "Jane Example",
    "default_from_email": "jane@example.com",
    "account_from_name": "Account Management",
    "account_from_email": "accounts@example.com",
    "account_reply_to_name": None,
    "account_reply_to_email": None,  # Set to None to not have any reply-to in account-related emails
    "company": "Khanna LLC",
    "company_address": "4445 Corporation Ln., Ste 264",  # Set to None to skip having an address.
    "company_city_state_zip": "Virginia Beach, VA 23462",
    "contact_email": "jane@example.com",
}


# Host-based alternate urlconfs.
# If the host matches one of these, use the alternate urlconf. Otherwise, use the ROOT_URLCONF.
# Every urlconf listed here must have a health_check endpoint for Render to deploy it.
# Every urlconf listed here must also have an "index" page to avoid infinite errors when rendering the 404 page.
ROOT_URLCONF = "config.urls"
HOST_URLCONFS: dict[str, str] = {}

# django-allauth
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
SESSION_COOKIE_AGE = 15_552_000  # 180 days
ACCOUNT_ADAPTER = "core.adapter.AccountAdapter"
LOGIN_REDIRECT_URL = "/accounts/settings/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_FORMS = {
    "login": "core.forms.LoginForm",
    "signup": "core.forms.SignupForm",
    "add_email": "allauth.account.forms.AddEmailForm",
    "change_password": "allauth.account.forms.ChangePasswordForm",
    "set_password": "allauth.account.forms.SetPasswordForm",
    "reset_password": "allauth.account.forms.ResetPasswordForm",
    "reset_password_from_key": "allauth.account.forms.ResetPasswordKeyForm",
    "disconnect": "allauth.socialaccount.forms.DisconnectForm",
}
## See https://django-allauth.readthedocs.io/en/latest/advanced.html#custom-user-models
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_PREVENT_ENUMERATION = False
ACCOUNT_SESSION_REMEMBER = True

PERMISSION_DENIED_REDIRECT = LOGIN_REDIRECT_URL

# django-allauth social
SOCIALACCOUNT_ADAPTER = "core.adapter.SocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
    "github": {},
}

# Event Handlers
EVENT_HANDLERS = {"default": "core.services.event_noop"}
EVENT_SECRET = env("EVENT_SECRET", default="insecure")

# Celery
CELERY_BROKER_URL = env("REDIS_URL", default=None)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_TIME_LIMIT = 60  # Raise exception after 60 seconds.
CELERY_WORKER_TASK_LOG_FORMAT = "[%(name)s] at=%(levelname)s timestamp=%(asctime)s processName=%(processName)s task_id=%(task_id)s task_name=%(task_name)s %(message)s"
CELERY_WORKER_LOG_FORMAT = "[%(name)s] at=%(levelname)s timestamp=%(asctime)s processName=%(processName)s %(message)s"
CELERY_WORKER_LOG_COLOR = False
CELERY_ACCEPT_CONTENT = ["json", "pickle"]
CELERY_TASK_SERIALIZER = "json"

# django-vite
DJANGO_VITE_ASSETS_PATH = BASE_DIR / "frontend/dist"
DJANGO_VITE_DEV_MODE = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}  # This is the default. Overriden by other settings later.


# LOGGING
LOGLEVEL = env("LOGLEVEL", default="INFO")

# See https://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/
# Django's default logger is painful and there's no good reason to merge with it.
LOGGING_CONFIG = None

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": "core.filters.RequestIDFilter"}},
        "formatters": {
            "default": {
                "format": "[%(name)s] at=%(levelname)s timestamp=%(asctime)s request_id=%(request_id)s "
                + "pathname=%(pathname)s funcname=%(funcName)s lineno=%(lineno)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "filters": ["request_id"],
                "formatter": "default",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "ERROR",  # Without this, it logs as a WARNING all 4xx requests.
                "propagate": False,
            },
            "": {"handlers": ["console"], "level": LOGLEVEL},
        },
    }
)
