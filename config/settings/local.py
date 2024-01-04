from .common import *

DEBUG = env("DJANGO_DEBUG", default=True)
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-v9@!9+-)rsufs7qy6j4ki-ywhggph**_^8h+-*zabvj314a**y",
)

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgresql://postgres@localhost:5432/postgres"
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# django-debug-toolbar
INSTALLED_APPS.append("debug_toolbar")
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]

# Postmark outputs JSON in test mode. Celery should treat that as info, not warning.
CELERY_WORKER_REDIRECT_STDOUTS_LEVEL = "INFO"

# django_vite
DJANGO_VITE["default"]["dev_mode"] = True
DJANGO_VITE["default"]["dev_server_port"] = env("VITE_PORT", default=3000)

# HTML validation middleware
# There's a longer default list, which we'll keep for testing.
CHECK_HTML_IGNORE_MESSAGES = [
    "proprietary attribute",
    "inserting implicit <p>",
    "trimming empty",
    "unescaped &",
    '<svg> attribute "stroke-width" has invalid value',
    "inserting missing 'title' element",
]
MIDDLEWARE.insert(-1, "check_html.CheckHTMLMiddleware")
