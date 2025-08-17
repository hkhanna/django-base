from freezegun import freeze_time
from django.test import override_settings
from django.utils import timezone
from django.urls import reverse
from django.test import Client
from django.conf import settings

from . import factories
from .. import services, selectors


def test_request_id_middleware_user(client, caplog, user):
    """The RequestIDMiddleware should set the User.id"""
    caplog.set_level("INFO")
    client.force_login(user)
    client.get(reverse("index"))
    assert f"User.id={user.pk}" in caplog.text


@override_settings(HEROKU=True)
def test_setremoteaddr_middleware(caplog):
    """An IP address passed in X-Forwarded-For header should end up in REMOTE_ADDR.
    We can only do this safely while using Heroku or Render. Ip should also end up in request log.
    """
    ip = factories.fake.ipv4()
    client = Client(HTTP_X_FORWARDED_FOR=ip)
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] == ip
    assert f"ip={ip}" in caplog.text


@override_settings(ENVIRONMENT="production")
def test_setremoteaddr_middleware_none(caplog):
    """No IP address in X-Forwarded-For makes REMOTE_ADDR None in prod."""
    client = Client()
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] is None
    assert "ip=None" in caplog.text


@override_settings(HEROKU=True)
def test_setremoteaddr_middleware_multiple(caplog):
    """Multiple IP addresses in X-Forwarded-For takes the first one since it is
    explicitly set by Render and can be trusted."""
    ip0 = factories.fake.ipv4()
    ip1 = factories.fake.ipv4()
    ip = f"{ip0}, {ip1}"
    client = Client(HTTP_X_FORWARDED_FOR=ip)
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] == ip1
    assert f"ip={ip1}" in caplog.text


def test_health_check(client):
    """Health check endpoint returns 200. Used for Render."""
    response = client.get("/health_check/")
    assert response.status_code == 200


@override_settings(
    HOST_URLCONFS={"www.example.com": "core.urls"},
    ALLOWED_HOSTS=["testserver", "www.example.com"],
)
def test_host_urlconf_middleware():
    """A matching host should set alternative urlconfs"""
    client = Client()
    response = client.get(reverse("index"))
    assert not hasattr(response.wsgi_request, "urlconf")  # No change (config.urls)

    client = Client(SERVER_NAME="www.example.com")
    response = client.get(reverse("index"))
    assert response.wsgi_request.urlconf == "core.urls"  # Directly use core.urls


@override_settings(MIDDLEWARE=settings.MIDDLEWARE + ["core.middleware.OrgMiddleware"])
def test_org_middleware_no_org_in_session(client, user):
    """If there's no org in the session, set the org to the most recently accessed, active org."""
    org1 = factories.org_create()
    org2 = factories.org_create()
    ou1 = services.org_user_create(
        org=org1, user=user
    )  # last_accessed_at set automatically
    ou2 = services.org_user_create(
        org=org2, user=user
    )  # last_accessed_at set automatically
    assert ou2.last_accessed_at > ou1.last_accessed_at

    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org2

    # More recently access the first org
    services.org_user_update(instance=ou1, last_accessed_at=timezone.now())
    assert ou2.last_accessed_at < ou1.last_accessed_at

    session = client.session
    session.clear()
    session.save()
    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org1

    # Deactivate the first Org
    services.org_update(instance=org1, is_active=False)

    session = client.session
    session.clear()
    session.save()
    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org2


@override_settings(MIDDLEWARE=settings.MIDDLEWARE + ["core.middleware.OrgMiddleware"])
def test_org_middleware_org_in_session(client, user):
    """If there's an org in the session on the same domain, set request.org to that org."""
    client.force_login(user)
    other_org = factories.org_create(
        owner=user,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == other_org


@override_settings(MIDDLEWARE=settings.MIDDLEWARE + ["core.middleware.OrgMiddleware"])
def test_org_middleware_in_session_on_different_domain(client, user, org):
    """If there's an org in the session on a different domain, ignore it."""
    client.force_login(user)
    other_org = factories.org_create(
        owner=user,
        is_active=True,
        domain="otherdomain.example.com",
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org
    session = client.session
    assert session["org_slug"] == org.slug


@override_settings(MIDDLEWARE=settings.MIDDLEWARE + ["core.middleware.OrgMiddleware"])
def test_org_middleware_org_in_session_bad(client, user, org):
    """If there's an org in the session, but it doesn't match the user, don't use it."""
    client.force_login(user)
    other_org = factories.org_create(
        owner=factories.user_create(),
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org
    assert response.wsgi_request.org != other_org


@override_settings(MIDDLEWARE=settings.MIDDLEWARE + ["core.middleware.OrgMiddleware"])
def test_org_middleware_ou_last_accessed(client, user, org):
    """Accessing an org should update the last_accessed_at field on the OrgUser."""
    client.force_login(user)
    org2 = factories.org_create(
        owner=user,
        is_active=True,
    )
    assert selectors.org_get_recent_for_user(user, org2.domain) == org2

    with freeze_time("2023-03-16 12:00:00Z"):
        response = client.get(reverse("index"))
        assert response.wsgi_request.org == org2
        ou = org2.org_users.get(user=user)
        assert ou.last_accessed_at == timezone.now()
        assert user.org_users.get(org=org).last_accessed_at != timezone.now()
