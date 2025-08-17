import re
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

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    # "backups": {
    #     "BACKEND": "django.core.files.storage.InMemoryStorage",
    # },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# This shouldn't be necessary since testing will substitute out the postmark
# backend for locmem, but this is just a precaution.
POSTMARK_TEST_MODE = True

# Test environment needs celery eager mode
CELERY_TASK_ALWAYS_EAGER = True

MIDDLEWARE.insert(1, "check_html.CheckHTMLMiddleware")

# django_vite
DJANGO_VITE["default"]["dev_mode"] = True
DJANGO_VITE["default"]["dev_server_port"] = env("VITE_PORT", default=3000)
