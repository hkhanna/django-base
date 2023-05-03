import factory.random
from .common import *

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

# Reproducable randomness for tests
factory.random.reseed_random(42)

# HTML validation middleware
MIDDLEWARE.insert(1, "check_html.CheckHTMLMiddleware")
