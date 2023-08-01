import re
from .test import *

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]

# Static file handling needs to be like production
DJANGO_VITE_DEV_MODE = False

# STATIC FILES - WHITENOISE
# The WhiteNoise middleware should go above everything else except the security middleware.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
# Allows WhiteNoise to compress and cache the static files
# FIXME - STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATIC_ROOT is where collectstatic dumps all the static files
STATIC_ROOT = BASE_DIR / ".playwright/staticfiles"
STATICFILES_DIRS = [BASE_DIR / "frontend/dist"]


# Vite generates files with 8 hash digits
def immutable_file_test(path, url):
    return re.match(r"^.+\.[0-9a-f]{8,12}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test
