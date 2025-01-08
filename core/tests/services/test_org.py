from unittest.mock import MagicMock
import pytest
from django.contrib.auth import get_user_model
import pytest

from .. import factories
from ... import models, services, selectors


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
        domain="example.com",
        primary_plan=factories.plan_create(),
        default_plan=factories.plan_create(),
    )
    assert org.org_users.filter(user=user, org=org).exists()


def test_org_switch(req, user, settings):
    """Switching an org sets request.org and returns the redirect url."""
    new_org = factories.org_create(owner=user, domain="newdomain.example.com")
    redirect_url = services.org_switch(request=req, slug=new_org.slug)
    assert req.org == new_org
    assert (
        redirect_url == f"{req.scheme}://{new_org.domain}" + settings.LOGIN_REDIRECT_URL
    )


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


def test_org_create_default_plan(user):
    """Creating an org with a missing primary_plan or default_plan will use or create a default plan"""
    assert selectors.plan_list().count() == 0
    org = services.org_create(name="Example Org", owner=user, domain="example.com")

    assert selectors.plan_list().count() == 1
    plan = selectors.plan_list().first()
    assert plan.is_default is True

    assert org.primary_plan == plan
    assert org.default_plan == plan
