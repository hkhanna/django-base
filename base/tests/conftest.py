import pytest
from .. import factories


@pytest.fixture
def user():
    user = factories.UserFactory()

    # Verify email address
    email_address = user.emailaddress_set.first()
    email_address.verified = True
    email_address.save()

    return user


@pytest.fixture
def org(user):
    return factories.OrgFactory(owner=user)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
