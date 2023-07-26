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

# django_vite
DJANGO_VITE_DEV_MODE = True

# Test environment needs celery eager mode
CELERY_TASK_ALWAYS_EAGER = True

# HTML validation middleware
CHECK_HTML_IGNORE_MESSAGES = list(CheckHTMLMiddleware.ignore_messages_default) + [
    '<svg> attribute "stroke-width" has invalid value',  # This is because of django-heroicons
]
MIDDLEWARE.insert(1, "check_html.CheckHTMLMiddleware")
