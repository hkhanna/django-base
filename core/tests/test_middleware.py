import logging
from freezegun import freeze_time
from django.test import override_settings
from django.utils import timezone
from django.urls import reverse
from django.test import Client
from . import factories
from .. import services


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


def test_route_flag(client, caplog):
    """If the socialaccount routes are accessed, something is wrong, so flag a Sentry error"""

    with caplog.at_level(logging.ERROR):
        client.get(reverse("socialaccount_connections"))
    assert (
        "A route in socialaccount was accessed that should not have been: "
        in caplog.text
    )


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


def test_org_middleware_no_org_in_session(client, user, org):
    """If there's no org in the session, set the org to the most recently accessed, active org."""
    client.force_login(user)
    personal = user.personal_org
    personal_ou = personal.org_users.get(user=user)
    ou = org.org_users.get(user=user)

    assert ou.last_accessed_at > personal_ou.last_accessed_at

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    # More recently access the personal org
    services.org_user_update(instance=personal_ou, last_accessed_at=timezone.now())
    assert ou.last_accessed_at < personal_ou.last_accessed_at

    session = client.session
    session.clear()
    session.save()
    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == personal

    # Deactivate the personal Org
    services.org_update(instance=personal, is_active=False)

    session = client.session
    session.clear()
    session.save()
    client.force_login(user)

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org


def test_org_middleware_org_in_session(client, user):
    """If there's an org in the session, set request.org to that org."""
    client.force_login(user)
    other_org = factories.org_create(
        owner=user,
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org == other_org


def test_org_middleware_org_in_session_bad(client, user):
    """If there's an org in the session, but it doesn't match the user, don't use it."""
    client.force_login(user)
    other_org = factories.org_create(
        owner=factories.user_create(),
        is_personal=False,
        is_active=True,
    )
    session = client.session
    session["org_slug"] = other_org.slug
    session.save()

    response = client.get(reverse("index"))
    assert response.wsgi_request.org != other_org


def test_org_middleware_ou_last_accessed(client, user, org):
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
