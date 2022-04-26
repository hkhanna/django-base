from .common import *
import re
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration


DEBUG = env("DJANGO_DEBUG", default=False)

# Heroku recommends this in the django-heroku package.
# Also, Heroku apparently takes care of this security issue.
ALLOWED_HOSTS = ["*"]

SECRET_KEY = env("DJANGO_SECRET_KEY")
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

# STATIC FILES - WHITENOISE
# The WhiteNoise middleware should go above everything else except the security middleware and cors middleware.
MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")
# Allows WhiteNoise to compress and cache the static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATIC_ROOT is where collectstatic dumps all the static files
STATIC_ROOT = BASE_DIR / "staticfiles"


# Vite generates files with 8 hash digits
def immutable_file_test(path, url):
    return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

# EMAIL - POSTMARK
EMAIL_BACKEND = "postmark.django_backend.EmailBackend"
POSTMARK_TEST_MODE = False

# Google Analytics
GA_TRACKING_ID = None  # Off by default

# Sentry
SENTRY_DSN = None  # Off by default
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        environment="production",
        traces_sample_rate=1.0,
        send_default_pii=True,
    )
