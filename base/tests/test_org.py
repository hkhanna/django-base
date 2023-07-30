import pytest
from datetime import timedelta
from pytest_django.asserts import assertRaisesMessage
from freezegun import freeze_time
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from ..models import Org, OrgUser, Plan, OrgInvitation, OUSetting, OrgUserOUSetting
from .assertions import assertMessageContains
import base.factories
from base import constants, services

User = get_user_model()


@pytest.fixture(autouse=True)
def ou_settings():
    # Permissive settings by default for test purposes
    OUSetting.objects.create(
        slug="can_invite_members",
        type=constants.SettingType.BOOL,
        default=1,
        owner_value=1,
    )


# FIXME do these belong in middleware tests?
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
    other_org = base.factories.org_create(
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
    other_org = base.factories.org_create(
        owner=base.factories.user_create(),
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org != other_org


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
