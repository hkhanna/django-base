import pytest
from .. import factories


@pytest.fixture
def user():
    return factories.UserFactory()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass
