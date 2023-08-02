import re
from .test import *

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# Turn off Vite HMR
DJANGO_VITE_DEV_MODE = False

# Point directly to manifest file so we don't need to collectstatic.
DJANGO_VITE_MANIFEST_PATH = BASE_DIR / "frontend/dist/manifest.json"

# STATIC FILES - WHITENOISE
# We cannot use fancy manifests or anything because the live_server fixture does not look in the build
# directory. It's a quirk of pytest-django. So we must use the django default storage backend.

# The WhiteNoise middleware should go above everything else except the security middleware.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
# STATIC_ROOT is where collectstatic dumps all the static files
STATIC_ROOT = (
    BASE_DIR / ".playwright"
)  # This isn't actually used because we never call collectstatic for playwright.
STATICFILES_DIRS = [BASE_DIR / "frontend/dist"]


# Vite generates files with 8 hash digits
def immutable_file_test(path, url):
    return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test