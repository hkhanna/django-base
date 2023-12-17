from django.core.exceptions import ImproperlyConfigured

from .common import *
import re
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


DEBUG = env("DJANGO_DEBUG", default=False)

# Production should be on one of Heroku or Render
RENDER = env("RENDER", default=False)
HEROKU = not RENDER

if HEROKU:
    # See https://devcenter.heroku.com/articles/http-request-id
    REQUEST_ID_HEADER = "X-Request-Id"  # type: ignore
    ALLOWED_HOSTS = ["*"]
elif RENDER:
    REQUEST_ID_HEADER = None
    ALLOWED_HOSTS = [
        "localhost"
    ]  # Add the custom domains in use here. Localhost is required by render during build to avoid a Sentry error.
    # Render doesn't provide an external hostname in, e.g., cron jobs.
    RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default=None)
    if RENDER_EXTERNAL_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

else:
    raise ImproperlyConfigured("Production should be on Heroku or Render.")


SECRET_KEY = env("DJANGO_SECRET_KEY")
EVENT_SECRET = env("EVENT_SECRET")
POSTMARK_API_KEY = env("POSTMARK_API_KEY")
# CELERY_BROKER_URL = env("REDIS_URL")

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# Allows db connections to remain open rather than closing them after each request
DATABASES["default"]["CONN_MAX_AGE"] = 60

# SECURITY
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")  # Force https
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60  # Set to 518400 once the app is being used
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": "django-base-production",
            "location": "media/",
            "default_acl": "private",
        },
    },
    # "backups": {
    #     "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    #     "OPTIONS": {
    #         "bucket_name": BACKUP BUCKET NAME,
    #         "location": "django-base/",
    #         "default_acl": "private",
    #     },
    # },
    "staticfiles": {
        # Allows WhiteNoise to compress and cache the static files
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# boto3 / django-storages
AWS_S3_ACCESS_KEY_ID = env("AWS_S3_ACCESS_KEY_ID")
AWS_S3_SECRET_ACCESS_KEY = env("AWS_S3_SECRET_ACCESS_KEY")

# STATIC FILES - WHITENOISE
# The WhiteNoise middleware should go above everything else except the security middleware.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_DIRS = [BASE_DIR / "frontend/dist"]


# Vite generates files with 8 hash digits
def immutable_file_test(path, url):
    return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

# EMAIL - POSTMARK
EMAIL_BACKEND = "postmark.django_backend.EmailBackend"
POSTMARK_TEST_MODE = False
POSTMARK_RETURN_MESSAGE_ID = True

# Sentry
SENTRY_DSN = None  # Off by default
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        environment="production",
        traces_sample_rate=1.0,
        send_default_pii=True,
    )
