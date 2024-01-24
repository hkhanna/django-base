from django.contrib.auth import get_user_model
import core.tests.factories
from core import services

User = get_user_model()


def test_owner_org_user(user):
    """Setting an Org owner automatically adds an OrgUser"""
    org = services.org_create(
        name="Example Org",
        owner=user,
        primary_plan=core.tests.factories.plan_create(),
        default_plan=core.tests.factories.plan_create(),
    )
    assert org.org_users.filter(user=user, org=org).exists()
