from django.contrib.auth import get_user_model
import core.tests.factories
from core import services

User = get_user_model()


def test_owner_org_user(user):
    """Setting an Org owner automatically adds an OrgUser"""
    org = services.org_create(
        name="Example Org",
        owner=user,
        is_personal=False,
        primary_plan=core.tests.factories.plan_create(),
        default_plan=core.tests.factories.plan_create(),
    )
    assert org.org_users.filter(user=user, org=org).exists()


def test_change_name_slug_personal(user, org):
    """Change an Org's slug when its name changes only if it's a personal Org."""
    personal = user.personal_org
    slug = personal.slug

    # No change to personal org name
    services.org_update(instance=personal)
    assert personal.slug == slug

    # Change to personal org name
    services.org_update(instance=personal, name="Example 123")
    assert personal.slug == "example-123"

    # Change to non-personal org name
    slug = org.slug
    services.org_update(instance=org, name="Example 456")
    assert org.slug == slug
