import pytest
from urllib import request
from django.conf import settings

from . import factories
from .. import models, constants


@pytest.fixture(scope="session")
def vite():
    """Ensures the vite server is running."""
    # Really only needed for playwright tests.
    try:
        request.urlopen(
            "http://localhost:" + str(settings.DJANGO_VITE_DEV_SERVER_PORT), timeout=1
        )
    except request.URLError as e:
        if not isinstance(e, request.HTTPError):
            raise Exception(
                "Vite server must be running on port "
                + str(settings.DJANGO_VITE_DEV_SERVER_PORT)
            ) from e


@pytest.fixture
def user():
    user = factories.user_create()

    # Verify email address
    email_address = user.emailaddress_set.first()
    email_address.verified = True
    email_address.save()

    return user


@pytest.fixture
def org(user):
    # User should be a non-owner member of the Org
    org = factories.org_create()
    models.OrgUser.objects.create(user=user, org=org)
    return org


@pytest.fixture
def ou(user, org):
    return user.org_users.get(org=org)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
