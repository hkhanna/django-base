import pytest
from .. import factories, models


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
    # User should be a non-owner member of the Org
    org = factories.OrgFactory()
    models.OrgUser.objects.create(user=user, org=org)
    return org


@pytest.fixture
def ou(user, org):
    return user.org_users.get(org=org)


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
