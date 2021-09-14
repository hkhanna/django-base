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

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sites",
    # Base must come before staticfiles because it overrides collectstatic
    # Base must come before allauth so that base templates take precedence
    "base.apps.BaseConfig",
    "django.contrib.staticfiles",
    "waffle",
    "tailwind",
    "heroicons",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
]

MIDDLEWARE = [
    "base.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "waffle.middleware.WaffleMiddleware",
]

ROOT_URLCONF = "config.urls"

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

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# My Additions
# ---------------------

# This is a good article for how to build custom users with the email as username
# inheriting from AbstractUser rather than AbstractUserBase:
# https://www.fomfus.com/articles/how-to-use-email-as-username-for-django-authentication-removing-the-username
AUTH_USER_MODEL = "base.User"
ATOMIC_REQUESTS = False
ENVIRONMENT = env.str("DJANGO_SETTINGS_MODULE").split(".")[-1]

# See https://devcenter.heroku.com/articles/http-request-id
REQUEST_ID_HEADER = "X-Request-Id"

# EMAIL
# If there's a POSTMARK_API_KEY (for the Sandbox server), use the Postmark backend.
# Otherwise, output to the console.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
POSTMARK_API_KEY = env("POSTMARK_API_KEY", default=None)
POSTMARK_TRACK_OPENS = False
if POSTMARK_API_KEY:
    EMAIL_BACKEND = "postmark.django_backend.EmailBackend"
    POSTMARK_TEST_MODE = False
MAX_SUBJECT_LENGTH = 78

# Site Configuration - Refactor this if >1 Site is hosted from this codebase.
SITE_ID = 1
SITE_CONFIG = {
    "name": "Base Django",
    "logo_url_link": "",
    "logo_url": "",
    "default_from_email": "Jane Example <jane@example.com>",
    "company": "Khanna Labs LLC",
    "company_address": "4445 Corporation Ln., Ste 264",
    "company_city_state_zip": "Virginia Beach, VA 23462",
    "contact_email": "jane@example.com",
}

# django-tailwind
TAILWIND_APP_NAME = "base"
INTERNAL_IPS = ["127.0.0.1"]

# django-allauth
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_ADAPTER = "base.adapter.AccountAdapter"
LOGIN_REDIRECT_URL = "/accounts/email/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_FORMS = {
    "login": "base.forms.LoginForm",
    "signup": "base.forms.SignupForm",
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

# django-waffle
WAFFLE_CREATE_MISSING_SWITCHES = True

# LOGGING
LOGLEVEL = env("LOGLEVEL", default="DEBUG")

# See https://www.caktusgroup.com/blog/2015/01/27/Django-Logging-Configuration-logging_config-default-settings-logger/
# Django's default logger is painful and there's no good reason to merge with it.
LOGGING_CONFIG = None

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": "base.filters.RequestIDFilter"}},
        "formatters": {
            "verbose": {
                "format": "[%(name)s] at=%(levelname)s timestamp=%(asctime)s request_id=%(request_id)s "
                + "pathname=%(pathname)s funcname=%(funcName)s lineno=%(lineno)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "simple": {
                "format": "[%(name)s] at=%(levelname)s timestamp=%(asctime)s request_id=%(request_id)s %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "filters": ["request_id"],
                "formatter": "verbose",
            },
            "request_log_handler": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "filters": ["request_id"],
                "formatter": "simple",
            },
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "ERROR",  # Without this, it logs as a WARNING all 4xx requests.
                "propagate": False,
            },
            "base-django.base.middleware": {
                "handlers": ["request_log_handler"],
                "level": LOGLEVEL,
                "propagate": False,
            },
            "base-django": {"handlers": ["console"], "level": LOGLEVEL},
        },
    }
)
