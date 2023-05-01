import logging
from django.test import override_settings
from django.urls import reverse
from django.test import Client
from ..factories import fake


def test_request_id_middleware_user(client, caplog, user):
    """The RequestIDMiddleware should set the User.id"""
    caplog.set_level("INFO")
    client.force_login(user)
    client.get(reverse("index"))
    assert f"User.id={user.pk}" in caplog.text


def test_setremoteaddr_middleware(caplog):
    """An IP address passed in X-Forwarded-For header should end up in REMOTE_ADDR.
    We can only do this safely while using Render. Ip should also end up in request log."""
    ip = fake.ipv4()
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


def test_setremoteaddr_middleware_multiple(caplog):
    """Multiple IP addresses in X-Forwarded-For takes the first one since it is
    explicitly set by Render and can be trusted."""
    ip0 = fake.ipv4()
    ip1 = fake.ipv4()
    ip = f"{ip0}, {ip1}"
    client = Client(HTTP_X_FORWARDED_FOR=ip)
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] == ip0
    assert f"ip={ip0}" in caplog.text


def test_health_check(client):
    """Health check endpoint returns 200"""
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
