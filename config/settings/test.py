import re
from .common import *
from check_html import CheckHTMLMiddleware

DEBUG = False
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-v9@!9+-)rsufs7qy6j4ki-ywhggph**_^8h+-*zabvj314a**y",
)
EVENT_SECRET = "test"

DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgresql://postgres@localhost:5432/postgres"
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# This shouldn't be necessary since testing will substitute out the postmark
# backend for locmem, but this is just a precaution.
POSTMARK_TEST_MODE = True

# Test environment needs celery eager mode
CELERY_TASK_ALWAYS_EAGER = True

# HTML validation middleware
CHECK_HTML_IGNORE_MESSAGES = list(CheckHTMLMiddleware.ignore_messages_default) + [
    '<svg> attribute "stroke-width" has invalid value',  # This is because of django-heroicons
]
MIDDLEWARE.insert(1, "check_html.CheckHTMLMiddleware")


# STATIC FILES - WHITENOISE
# We cannot use fancy manifests or anything because the live_server fixture does not look in the build
# directory. It's a quirk of pytest-django. So we must use the django default storage backend.

# The WhiteNoise middleware should go above everything else except the security middleware.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# STATIC_ROOT is where collectstatic dumps all the static files
# This isn't actually used because we never call collectstatic for playwright.
# But we need to use a real directory like .venv to avoid getting a bunch of warnings about a non-existent directory.
STATIC_ROOT = BASE_DIR / ".venv"
STATICFILES_DIRS = [BASE_DIR / "frontend/dist"]


# Vite generates files with 8 hash digits
def immutable_file_test(path, url):
    return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

# Turn off Vite HMR
DJANGO_VITE_DEV_MODE = False

# Point directly to manifest file so we don't need to collectstatic.
DJANGO_VITE_MANIFEST_PATH = BASE_DIR / "frontend/dist/manifest.json"
