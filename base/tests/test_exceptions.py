from unittest.mock import Mock
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from ..views import IndexView
from .assertions import assertMessageContains


def test_permission_denied_default(client, settings, monkeypatch):
    """PermissionDenied exception redirects by default to PERMISSION_DENIED_REDIRECT"""
    message = "You are a a nice person, but you don't have access to this."
    monkeypatch.setattr(
        IndexView, "get_context_data", Mock(side_effect=PermissionDenied(message))
    )
    response = client.get(reverse("index"))
    assert response.status_code == 302
    assert response.url == settings.PERMISSION_DENIED_REDIRECT
    assertMessageContains(response, message)


def test_permission_denied_redirect(client, monkeypatch):
    """PermissionDenied exception can take an optional url to redirect to"""
    message = "You are a a nice person, but you don't have access to this."
    url = reverse("terms_of_use")
    monkeypatch.setattr(
        IndexView, "get_context_data", Mock(side_effect=PermissionDenied(message, url))
    )
    response = client.get(reverse("index"))
    assert response.status_code == 302
    assert response.url == url
    assertMessageContains(response, message)
