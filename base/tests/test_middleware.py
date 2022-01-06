from django.test import override_settings
from django.urls import reverse
from django.test import Client
from ..factories import fake


def test_setremoteaddr_middleware():
    """An IP address passed in X-Forwarded-For header should end up in REMOTE_ADDR.
    We can only do this safely while using Heroku."""
    ip = fake.ipv4()
    client = Client(HTTP_X_FORWARDED_FOR=ip)
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] == ip


@override_settings(ENVIRONMENT="production")
def test_setremoteaddr_middleware_none():
    """No IP address in X-Forwarded-For makes REMOTE_ADDR None in prod."""
    client = Client()
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] is None


def test_setremoteaddr_middleware_multiple():
    """Multiple IP addresses in X-Forwarded-For takes the last one since it is the
    only one set by Heroku and can be trusted."""
    ip0 = fake.ipv4()
    ip1 = fake.ipv4()
    ip = f"{ip0}, {ip1}"
    client = Client(HTTP_X_FORWARDED_FOR=ip)
    response = client.get(reverse("index"))
    request = response.wsgi_request
    assert request.META["REMOTE_ADDR"] == ip1
