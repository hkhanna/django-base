import pytest
from pytest_django.asserts import assertRaisesMessage
from freezegun import freeze_time
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from ..models import Org, Plan
import base.factories

User = get_user_model()


def test_switch_org(client, user, org):
    """Switching an org simply sets request.org and persists that information to the session."""
    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    response = client.post(reverse("org_switch"), {"slug": user.personal_org.slug})
    assert response.wsgi_request.org == user.personal_org
    assert response.wsgi_request.session["org_slug"] == user.personal_org.slug


def test_switch_inactive_org(client, user, org):
    """A user may not switch to an inactive org"""
    personal = user.personal_org
    personal.is_active = False
    personal.full_clean()
    personal.save()

    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    response = client.post(reverse("org_switch"), {"slug": personal.slug})
    assert response.wsgi_request.org == org
    assert response.wsgi_request.session["org_slug"] == org.slug


def test_switch_inactive_unauthorized(client, user):
    """A user may not switch to an org that they don't belong to."""
    org = base.factories.OrgFactory()  # Different owner

    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == user.personal_org

    response = client.post(reverse("org_switch"), {"slug": org.slug})
    assert response.wsgi_request.org == user.personal_org
    assert response.wsgi_request.session["org_slug"] == user.personal_org.slug


def test_one_org(user):
    """A user must belong to at least one Org."""
    user.orgs.clear()
    with assertRaisesMessage(
        ValidationError, "A user must belong to at least one organization."
    ):
        user.full_clean()


def test_auto_create_org():
    """Creating a user creates their personal organization"""
    assert Org.objects.count() == 0
    user = User.objects.create(
        first_name="First", last_name="Last", email="first@example.com"
    )

    assert Org.objects.count() == 1
    org = Org.objects.first()
    assert org.owner == user
    assert org.is_personal is True
    assert org.is_active is True
    assert list(org.users.all()) == [user]


def test_owner_org_user(user, settings):
    """Setting an Org owner automatically adds an OrgUser"""
    org = Org(
        name="Example Org",
        owner=user,
        is_personal=False,
        primary_plan=base.factories.PlanFactory(),
        default_plan=base.factories.PlanFactory(),
    )
    org.full_clean()
    org.save()
    assert org.org_users.filter(user=user, org=org).exists()


def test_maximum_personal(user):
    """User can have a maximum of 1 personal, active org."""
    # A user doesn't necessarily have to have a personal org.
    # Think a corporate rank-and-file employee who was invited by their company admin.
    assert Org.objects.filter(owner=user, is_personal=True).count() == 1

    org = Org(
        owner=user,
        is_personal=False,
        name=user.name,
        primary_plan=base.factories.PlanFactory(),
        default_plan=base.factories.PlanFactory(),
    )
    org.full_clean()  # OK
    org.save()  # OK

    org = Org(
        owner=user,
        is_personal=True,
        is_active=False,
        name=user.name,
        primary_plan=base.factories.PlanFactory(),
        default_plan=base.factories.PlanFactory(),
    )
    org.full_clean()  # OK
    org.save()  # OK

    org = Org(
        owner=user,
        is_personal=True,
        name=user.name,
        primary_plan=base.factories.PlanFactory(),
        default_plan=base.factories.PlanFactory(),
    )
    with assertRaisesMessage(IntegrityError, "unique_personal_active_org"):
        org.full_clean()
        org.save()


def test_no_org_in_session(client, user, org):
    """If there's no org in the session, set the org to the most recently accessed, active org."""
    client.force_login(user)
    personal = user.personal_org
    personal_ou = personal.org_users.get(user=user)
    ou = org.org_users.get(user=user)

    assert ou.last_accessed_at > personal_ou.last_accessed_at

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    # More recently access the personal org
    personal_ou.last_accessed_at = timezone.now()
    personal_ou.full_clean()
    personal_ou.save()

    assert ou.last_accessed_at < personal_ou.last_accessed_at

    session = client.session
    session.clear()
    session.save()
    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == personal

    # Deactivate the personal Org
    personal.is_active = False
    personal.full_clean()
    personal.save()

    session = client.session
    session.clear()
    session.save()
    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org


def test_org_in_session(client, user):
    """If there's an org in the session, set request.org to that org."""
    client.force_login(user)
    other_org = base.factories.OrgFactory(
        owner=user,
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == other_org


def test_org_in_session_bad(client, user):
    """If there's an org in the session, but it doesn't match the user, don't use it."""
    client.force_login(user)
    other_org = base.factories.OrgFactory(
        owner=base.factories.UserFactory(),
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org != other_org


def test_change_user_name_org_name(user):
    """Changing a user's name should change the name of the user's personal org."""
    user.first_name = "Kipp"
    user.full_clean()
    user.save()

    assert user.personal_org.name == user.name


def test_change_name_slug_personal(user, org):
    """Change an Org's slug when its name changes only if it's a personal Org."""
    personal = user.personal_org
    slug = personal.slug

    # No change to personal org name
    personal.full_clean()
    personal.save()
    assert personal.slug == slug

    # Change to personal org name
    personal.name = "Example 123"
    personal.full_clean()
    personal.save()
    assert personal.slug == "example-123"

    # Change to non-personal org name
    slug = org.slug
    org.name = "Example 456"
    org.full_clean()
    org.save()
    assert org.slug == slug


def test_ou_last_accessed(client, user, org):
    client.force_login(user)
    assert user.default_org == org

    with freeze_time("2023-03-16 12:00:00Z") as frozen_dt:
        response = client.get(reverse("index"))
        assert response.wsgi_request.org == org
        ou = org.org_users.get(user=user)
        assert ou.last_accessed_at == timezone.now()
        assert (
            user.org_users.get(org=user.personal_org).last_accessed_at != timezone.now()
        )


def test_org_detail(client, user, org):
    """Org detail page shows members"""
    client.force_login(user)
    assert user.default_org == org
    other_user = base.factories.UserFactory()
    org.users.add(other_user)

    response = client.get(reverse("org_detail"))
    assert response.status_code == 200
    assert user.name in str(response.content)
    assert "Owner" in str(response.content)
    assert other_user.name in str(response.content)


def test_plan_default_unique(user):
    """Setting a plan as default unsets default from all other plans."""
    assert Plan.objects.count() == 1  # default plan created when User was created
    assert Plan.objects.first().is_default is True

    plan = base.factories.PlanFactory()
    plan.is_default = True
    plan.save()

    assert user.personal_org.primary_plan.is_default is False  # Default flipped off
    assert plan.is_default is True  # Default turned on


@pytest.mark.skip("Not implemented")
def test_send_invitation():
    """Inviting a user"""


@pytest.mark.skip("Not implemented")
def test_invite_existing_user():
    """Inviting an existing user sends them an email ??"""


@pytest.mark.skip("Not implemented")
def test_invite_new_user():
    """"""


@pytest.mark.skip("Not implemented")
def test_invite_permission():
    """"""


@pytest.mark.skip("Not implemented")
def test_remove_user():
    """"""


@pytest.mark.skip("Not implemented")
def test_remove_permission():
    """"""


@pytest.mark.skip("Not implemented")
def test_remove_owner():
    """An org owner may not be removed"""


# ideas for OUSettings
# can_invite_members
# can_remove_members
# can_change_org_name

# ideas for OrgSettings
# members_can_leave

# DREAM: Org views
# - invitations
#   - If you created your user account because you were invited, don't create a personal org automatically.
#   - If you don't have a personal org, there should be a way to create one.
# - Removing a user from an org creates a personal org for them if they would otherwise have no active orgs.

# Org CRUD tests
"""A user may create an Org"""
"""A user may not own more than 10 Orgs"""
"""Deleting an Org sets is_active to False"""
"""Only an owner may delete an Org and then only if the Org allows it."""
"""Org information like name may be updated with the can_change_org_name OUSetting"""

# Tests related to deleting a User
"""Can't delete your account if you own an org, unless its your personal Org"""
"""Deleting your account deactivates your personal org."""
"""Undeleting your account creates a new personal Org"""

# Tests related to transfering an org
"""An owner may transfer ownership of an org"""
"""A personal org may not be transfered"""

# Tests related to leaving an org
"""A user may leave an org -- should this be on an org-by-org basis?"""
"""An owner may not leave an org"""
