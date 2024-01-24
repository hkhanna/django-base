from django.conf import settings
from django.test import override_settings
import pytest
from django.urls import reverse

from .. import factories
from ... import views, services, selectors, constants


@pytest.fixture(autouse=True)
def org_middleware():
    with override_settings(
        MIDDLEWARE=settings.MIDDLEWARE + ["core.middleware.OrgMiddleware"]
    ):
        yield


def test_org_switch(client, user, org):
    """Switching an org simply sets request.org and persists that information to the session."""
    new_org = factories.org_create(owner=user)

    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == new_org

    response = client.post(reverse("org_switch"), {"slug": org.slug})
    assert response.wsgi_request.org == org
    assert response.wsgi_request.session["org_slug"] == org.slug


def test_org_switch_inactive(client, user, org):
    """A user may not switch to an inactive org"""
    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    new_org = factories.org_create(owner=user)
    services.org_update(instance=new_org, is_active=False)

    response = client.post(reverse("org_switch"), {"slug": new_org.slug})
    assert response.status_code == 404
    assert response.wsgi_request.org == org
    assert response.wsgi_request.session["org_slug"] == org.slug


def test_org_switch_inactive_unauthorized(client, user, org):
    """A user may not switch to an org that they don't belong to."""
    other_org = factories.org_create()  # Different owner

    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    response = client.post(reverse("org_switch"), {"slug": other_org.slug})
    assert response.status_code == 404
    assert response.wsgi_request.org == org
    assert response.wsgi_request.session["org_slug"] == org.slug


def test_org_user_setting_permission_mixin(rf, user, org):
    """The OrgUserSettingPermissionMixin is a mixin that requires a given OrgUserSetting to be True."""
    org_user_setting = services.org_user_setting_create(
        type=constants.SettingType.BOOL,
        slug="test_setting",
        default="false",
        owner_value="true",
    )
    mixin = views.OrgUserSettingPermissionMixin()
    mixin.org_user_setting = "test_setting"
    request = rf.post("/test")
    request.user = user
    request.org = org
    mixin.request = request
    assert mixin.test_func() is False

    # Now, give the user the permission.
    org_user = selectors.org_user_list(org=org, user=user).get()
    org_user_org_user_setting = services.org_user_org_user_setting_create(
        org_user=org_user, setting=org_user_setting, value="true"
    )
    assert mixin.test_func() is True
