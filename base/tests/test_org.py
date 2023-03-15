from pytest_django.asserts import assertRaisesMessage
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from ..models import Org
import base.factories

User = get_user_model()


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
    org = Org(name="Example Org", owner=user, is_personal=False)
    org.full_clean()
    org.save()
    assert org.org_users.filter(
        user=user, org=org, role=settings.DEFAULT_ORG_OWNER_ROLE
    ).exists()


def test_owner_org_user_role(user, settings):
    """Setting an Org owner automatically updates an OrgUser's role to settings.DEFAULT_ORG_OWNER_ROLE"""
    org = Org.objects.create(name="Example Org", owner=user, is_personal=False)
    ou = org.org_users.filter(org=org, role=settings.DEFAULT_ORG_OWNER_ROLE)
    assert len(ou) == 1
    assert ou.first().user == user

    # Create a new user and add them to the Org as a member
    new_user = base.factories.UserFactory()
    org.users.add(new_user, through_defaults={"role": settings.DEFAULT_ORG_ROLE})
    assert org.org_users.filter(user=new_user).count() == 1
    assert (
        org.org_users.filter(user=new_user, role=settings.DEFAULT_ORG_ROLE).count() == 1
    )

    # Transfer ownership to a new user
    org.owner = new_user
    org.full_clean()
    org.save()
    assert org.org_users.filter(user=new_user).count() == 1
    assert (
        org.org_users.filter(
            user=new_user, role=settings.DEFAULT_ORG_OWNER_ROLE
        ).count()
        == 1
    )


def test_maximum_personal(user):
    """User can have a maximum of 1 personal, active org."""
    # A user doesn't necessarily have to have a personal org.
    # Think a corporate rank-and-file employee who was invited by their company admin.
    assert Org.objects.filter(owner=user, is_personal=True).count() == 1

    org = Org(owner=user, is_personal=False, name=user.name)
    org.full_clean()  # OK
    org.save()  # OK

    org = Org(owner=user, is_personal=True, is_active=False, name=user.name)
    org.full_clean()  # OK
    org.save()  # OK

    org = Org(owner=user, is_personal=True, name=user.name)
    with assertRaisesMessage(IntegrityError, "unique_personal_org"):
        org.full_clean()
        org.save()


def test_no_org_in_session(client, user):
    """If there's no org in the session, set the org to the user's personal org, or if none, the most recently updated org."""
    client.force_login(user)

    # There's only 1 Org and it's the user's personal Org
    assert Org.objects.count() == 1
    personal_org = Org.objects.filter(
        owner=user, is_personal=True, is_active=True
    ).first()
    assert personal_org is not None

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == personal_org

    # Add a non-personal Org
    other_org = Org.objects.create(owner=user, is_personal=False, is_active=True)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == personal_org

    # Deactivate the personal Org
    personal_org.is_active = False
    personal_org.full_clean()
    personal_org.save()
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == other_org


def test_org_in_session(client, user):
    """If there's an org in the session, set request.org to that org."""
    client.force_login(user)
    other_org = Org.objects.create(
        name="Example Org",
        slug="example-org",
        owner=user,
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = "example-org"
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == other_org


def test_org_in_session_bad(client, user):
    """If there's an org in the session, but it doesn't match the user, don't use it."""
    client.force_login(user)
    other_org = Org.objects.create(
        name="Example Org",
        slug="example-org",
        owner=base.factories.UserFactory(),
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = "example-org"
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org != other_org


def test_switch_org():
    """Switching an org simply sets request.org and persists that information to the session."""
    assert False


def test_switch_inactive_org():
    """A user may not switch to an inactive org"""
    assert False


def test_email_message_track_org():
    """EmailMessage should track the active org when sent"""
    assert False


def test_change_user_name_org_name():
    """Changing a user's name should change the name of the user's personal org."""
    assert False


# DREAM: Org views
# - creating an org
# - deleting an org
# - transfer org ownership
#   - A user may not transfer ownership of a personal org
# - Convert personal org into a non-personal org
# - invitations
#   - If you created your user account because you were invited, don't create a personal org automatically.
#   - If you don't have a personal org, there should be a way to create one.
# - Removing a user from an org creates a personal org for them if they would otherwise have no active orgs.

# Tests related to deleting a User
"""Can't delete your account if you own an org, unless its your personal Org"""
"""Deleting your account deactivates your personal org."""
"""Undeleting your account creates a new personal Org"""
