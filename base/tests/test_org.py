from pytest_django.asserts import assertRaisesMessage
from django.urls import reverse
from django.core.exceptions import ValidationError
import base.constants
import base.factories
from ..models import Org, OrgUser


def test_one_owner(user):
    """An Org must have at least one owner."""
    org = Org(name="Example Organization")
    org.full_clean()
    org.save()  # OK because owner validation happens at the OrgUser level.

    # 0 owners
    ou = OrgUser(user=user, org=org, role="something")
    with assertRaisesMessage(ValidationError, "Organization must have an owner."):
        ou.full_clean()

    # 1 owner
    ou = OrgUser(user=user, org=org, role=base.constants.OrgUser.Role.OWNER)
    ou.full_clean()  # OK
    ou.save()

    # 2 owners
    ou = OrgUser(
        user=base.factories.UserFactory(),
        org=org,
        role=base.constants.OrgUser.Role.OWNER,
    )
    ou.full_clean()  # OK
    ou.save()


def test_one_org(user):
    """A user must belong to at least one Org."""
    user.orgs.clear()
    with assertRaisesMessage(
        ValidationError, "A user must belong to at least one organization."
    ):
        user.full_clean()


def test_auto_create_org():
    """Creating a user creates their personal organization"""


"""Switch orgs -- only allow switch to active"""


"""Deleting a user inactivates their personal organization if they have one"""

"""Create an org?"""
"""Delete an org?"""
"""Invite to org?"""
"""Can't delete your account if you own an org, unless its your personal Org.?"""
"""Transfer ownership?"""
"""Transfering a personal org creates a new personal org for yourself and removes the personal flag on the transfered org"""
"""EmailMessage should track the active org when sent"""
"""The owner must also be an OrgUser"""
