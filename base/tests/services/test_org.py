import pytest
from datetime import timedelta
from pytest_django.asserts import assertRaisesMessage
from freezegun import freeze_time
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from ..assertions import assertMessageContains
import base.tests.factories
from base import constants, services

User = get_user_model()


def test_owner_org_user(user):
    """Setting an Org owner automatically adds an OrgUser"""
    org = services.org_create(
        name="Example Org",
        owner=user,
        is_personal=False,
        primary_plan=base.tests.factories.plan_create(),
        default_plan=base.tests.factories.plan_create(),
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


# N.B. Holding off on developing these features until there's some concrete direction.

# Org CRUD tests
"""A user may create an Org"""
"""If you don't have a personal org, there should be a way to create one. -- although this shouldn't always be available. Could be an OrgSetting."""
"""A user may not own more than 10 Orgs"""
"""Deleting an Org sets is_active to False"""
"""Only an owner may delete an Org and then only if the Org allows it."""
"""Org information like name may be updated with the `can_change_org_name` OrgUserSetting"""

# Tests related to deleting a User
"""Can't delete your account if you own an org, unless its your personal Org"""
"""Deleting your account deactivates your personal org."""
"""Undeleting your account creates a new personal Org"""

# Tests related to transfering an org
"""An owner may transfer ownership of an org"""
"""A personal org may not be transfered"""

# Tests related to leaving an org
"""A user may leave an org -- should this be on an org-by-org basis with a `members_can_leave` OrgSetting?"""
"""An owner may not leave an org"""
"""If a user leaves an org and have no active orgs, it auto-creates a personal org."""
