from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.asserts import assertRaisesMessage

from base import factories, services

from ...exceptions import ApplicationError, ApplicationWarning
from ...models import OrgInvitation

User = get_user_model()


def test_org_invitation_validate_new(org, user):
    """Given an unsaved instance of org_invitation with only an email,
    combine it with the requesting user and their org."""

    org_invitation = services.org_invitation_create(
        save=False, email=factories.fake.email()
    )
    org_invitation = services.org_invitation_validate_new(
        org=org, created_by=user, org_invitation=org_invitation
    )
    assert org_invitation.org == org
    assert org_invitation.created_by == user
    assert org_invitation._state.adding is False


def test_org_invite_duplicate_user(user, org):
    """Inviting a user that is already in the Org will raise an ApplicationError."""

    new = factories.user_create()
    services.org_user_create(org=org, user=new)
    org_invitation = services.org_invitation_create(save=False, email=new.email)

    with assertRaisesMessage(
        ApplicationError, f"{new.email} is already a member of {org.name}."
    ):
        services.org_invitation_validate_new(
            org=org, created_by=user, org_invitation=org_invitation
        )


def test_org_invite_duplicate_invitation(user, org):
    """Inviting a user that has an open invitation will raise an ApplicationWarning."""
    new = factories.user_create()
    services.org_invitation_create(save=True, email=new.email, org=org, created_by=user)
    duplicate = services.org_invitation_create(save=False, email=new.email)

    with assertRaisesMessage(
        ApplicationWarning, f"{new.email} already has an invitation to {org.name}."
    ):
        services.org_invitation_validate_new(
            org=org, created_by=user, org_invitation=duplicate
        )


def test_org_invitation_send(org, user, mailoutbox, settings):
    """Given a validated, saved Org Invitation, send the email to the invitee."""
    email = factories.fake.email()
    org_invitation = services.org_invitation_create(
        email=email, org=org, created_by=user
    )
    services.org_invitation_send(org_invitation=org_invitation)

    assert OrgInvitation.objects.count() == 1
    invitation = OrgInvitation.objects.first()
    assert invitation.status == "Sent"
    assert invitation.email_messages.count() == 1
    assert invitation.invitee is None  # No existing user
    assert len(mailoutbox) == 1
    assert email in mailoutbox[0].to[0]
    assert (
        f"Invitation to join {org.name} on {settings.SITE_CONFIG['name']}"
        in mailoutbox[0].subject
    )
    assert "accept" in mailoutbox[0].body


def test_org_invite_resend(org, user, mailoutbox):
    """Resend invitation email."""
    org_invitation = services.org_invitation_create(
        email=factories.fake.email(), org=org, created_by=user
    )
    services.org_invitation_send(org_invitation=org_invitation)
    assert OrgInvitation.objects.first().email_messages.count() == 1
    assert len(mailoutbox) == 1

    # Avoid EmailMessage cooldown
    with freeze_time(timezone.now() + timedelta(hours=1)):
        services.org_invitation_resend(org=org, uuid=org_invitation.uuid)
        assert OrgInvitation.objects.first().email_messages.count() == 2
        assert len(mailoutbox) == 2


@pytest.mark.skip("Not implemented")
def test_invite_new_user_accept():
    """"""
    # Make sure OrgInvitation.invitee is set to the user.


@pytest.mark.skip("Not implemented")
def test_invite_new_user_accept_no_personal():
    """If you created your user account because you were invited, don't create a personal org automatically."""


@pytest.mark.skip("Not implemented")
def test_invite_existing_user_accept():
    """"""
    # Make sure OrgInvitation.invitee is set to the user.


@pytest.mark.skip("Not implemented")
def test_remove_user():
    """"""


@pytest.mark.skip("Not implemented")
def test_remove_user_last_org():
    """Removing a user from an org creates a personal org for them if they would otherwise have no active orgs."""


@pytest.mark.skip("Not implemented")
def test_remove_permission():
    """"""


@pytest.mark.skip("Not implemented")
def test_remove_owner():
    """An org owner may not be removed"""


# Org invitations
"""Disallow resending an invitation more than `max_invitation_resend` OrgSetting times."""
"""Inviter must have a verified email before they may invite anyone."""
