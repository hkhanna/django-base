import pytest
from django.urls import reverse

from .. import models


@pytest.mark.skip
def test_get_settings(client, user):
    """Settings page should contain the user's information."""
    response = client.get(reverse("account_settings"))
    assert user.first_name in str(response.content)
    assert user.last_name in str(response.content)
    assert user.email in str(response.content)


def test_change_password_happy(client, user):
    """User can change their password."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "goodpass",
        "password1": "newpass123",
        "password2": "newpass123",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "Password successfully changed" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is True
    assert client.login(username=user.email, password="goodpass") is False


def test_change_password_incorrect(client, user):
    """User must provide their current password to change it."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "bad",
        "password1": "newpass123",
        "password2": "newpass123",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "type your current password" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="goodpass") is True


def test_change_password_match(client, user):
    """User's new passwords must match to change them."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "goodpass",
        "password1": "newpass123",
        "password2": "differentpass123",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "You must type the same password each time" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="differentpass123") is False
    assert client.login(username=user.email, password="goodpass") is True
