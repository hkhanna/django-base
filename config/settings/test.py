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

DJANGO_VITE_DEV_MODE = env("VITE_DEV_MODE", default=True)
DJANGO_VITE_DEV_SERVER_PORT = env("VITE_PORT", default=3000)

# If we're not using vite dev server, we need to serve static files from
# whitenoise.
# We only use this in CI because we are rebuilding the Vite files right before running
# the tests, and tests seems to be flaky in CI without it.
if not DJANGO_VITE_DEV_MODE:
    # Point directly to manifest file so we don't need to collectstatic.
    DJANGO_VITE_MANIFEST_PATH = BASE_DIR / "frontend/dist/manifest.json"

    # STATIC FILES - WHITENOISE
    # The WhiteNoise middleware should go above everything else except the security middleware.
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
    # STATIC_ROOT is where collectstatic dumps all the static files
    # However, since we're not running collectstatic here, so we just need to pick
    # a directory that exists and has very few files in it to avoid slowing down tests.
    STATIC_ROOT = BASE_DIR / ".github"
    STATICFILES_DIRS = [BASE_DIR / "frontend/dist"]

    # Vite generates files with 8 hash digits
    def immutable_file_test(path, url):
        return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)

    WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test
