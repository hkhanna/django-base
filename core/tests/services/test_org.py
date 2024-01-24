from unittest.mock import MagicMock
import pytest
from django.contrib.auth import get_user_model
import pytest

from .. import factories
from ... import models, services


User = get_user_model()


@pytest.fixture
def req(rf, user, org):
    req = rf.get("/")
    req.session = MagicMock()
    req.user = user
    req.org = org
    return req


def test_owner_org_user(user):
    """Setting an Org owner automatically adds an OrgUser"""
    org = services.org_create(
        name="Example Org",
        owner=user,
        primary_plan=factories.plan_create(),
        default_plan=factories.plan_create(),
    )
    assert org.org_users.filter(user=user, org=org).exists()


def test_org_switch(req, user):
    """Switching an org simply sets request.org.
    It will be persisted to the session by the middleware."""
    new_org = factories.org_create(owner=user)
    services.org_switch(request=req, slug=new_org.slug)
    assert req.org == new_org


def test_org_switch_inactive(req, user, org):
    """A user may not switch to an inactive org"""
    new_org = factories.org_create(owner=user)
    services.org_update(instance=new_org, is_active=False)

    with pytest.raises(models.Org.DoesNotExist):
        services.org_switch(request=req, slug=new_org.slug)

    assert req.org == org


def test_org_switch_inactive_unauthorized(req, user, org):
    """A user may not switch to an org that they don't belong to."""
    assert req.user == user
    other_org = factories.org_create()  # Different owner

    with pytest.raises(models.Org.DoesNotExist):
        services.org_switch(request=req, slug=other_org.slug)

    assert req.org == org
