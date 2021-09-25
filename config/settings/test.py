import factory.random
from .common import *

DEBUG = False
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="django-insecure-v9@!9+-)rsufs7qy6j4ki-ywhggph**_^8h+-*zabvj314a**y",
)

DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgresql://postgres@localhost:5432/postgres"
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = False

# Prevent log spew during testing
LOGLEVEL = env("LOGLEVEL", default="CRITICAL")
logging.getLogger("django").setLevel(LOGLEVEL)
logging.getLogger("").setLevel(LOGLEVEL)
logging.getLogger("base.middleware").setLevel(LOGLEVEL)

# This shouldn't be necessary since testing will substitute out the postmark
# backend for locmem, but this is just a precaution.
POSTMARK_TEST_MODE = True


# Reproducable randomness for tests
factory.random.reseed_random(42)