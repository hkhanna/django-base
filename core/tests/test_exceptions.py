from unittest.mock import Mock
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from ..views import ProfileView
from .assertions import assertMessageContains


def test_permission_denied_default(client, user, settings, monkeypatch):
    """PermissionDenied exception redirects by default to PERMISSION_DENIED_REDIRECT"""
    message = "You are a a nice person, but you don't have access to this."
    monkeypatch.setattr(ProfileView, "get", Mock(side_effect=PermissionDenied(message)))
    client.force_login(user)
    response = client.get(reverse("user:profile"))
    assert response.status_code == 302
    assert response.url == settings.PERMISSION_DENIED_REDIRECT
    assertMessageContains(response, message)


def test_permission_denied_redirect(client, user, monkeypatch):
    """PermissionDenied exception can take an optional url to redirect to"""
    message = "You are a a nice person, but you don't have access to this."
    url = reverse("terms_of_use")
    monkeypatch.setattr(
        ProfileView, "get", Mock(side_effect=PermissionDenied(message, url))
    )
    client.force_login(user)
    response = client.get(reverse("user:profile"))
    assert response.status_code == 302
    assert response.url == url
    assertMessageContains(response, message)


def test_404(client):
    response = client.get("badurl/")
    assert response.status_code == 404
    assert "404" in str(response.content)
