from django.urls import reverse
from allauth.account import models as auth_models, utils as auth_utils

from .. import models, factories


def test_get_settings(client, user):
    """Settings page should contain the user's information."""
    client.force_login(user)
    response = client.get(reverse("account_settings"))
    assert user.first_name in str(response.content)
    assert user.last_name in str(response.content)
    assert user.email in str(response.content)


def test_change_info(client, user):
    """User can change their personal info"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "Personal information saved" in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] == user.first_name
    assert payload["last_name"] == user.last_name
    assert payload["email"] == user.email


def test_change_info_bad(client, user):
    """User must provide their current password to change their personal info"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "badpass",
        "form_name": "pi",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "type your current password" in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] != user.first_name
    assert payload["last_name"] != user.last_name
    assert payload["email"] != user.email


def test_change_email_sync(client, user):
    """A changed User email address should keep EmailAddress in sync with User.email"""
    auth_utils.sync_user_email_addresses(user)
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    email_address = auth_models.EmailAddress.objects.get(user=user)
    assert email_address.email == payload["email"]


def test_change_email_confirm(client, user):
    """A changed User email address should send a confirmation email"""
    auth_utils.sync_user_email_addresses(user)
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    email_message = models.EmailMessage.objects.filter(created_by=user).first()
    assert email_message.to_email == payload["email"]


def test_no_email_change(client, user):
    """A personal information update that does not update the user's email
    (case insensitive) should not send a confirmation email"""
    auth_utils.sync_user_email_addresses(user)
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": user.email.upper(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    assert models.EmailMessage.objects.filter(created_by=user).exists() is False


def test_email_lowercase(client, user):
    """Email address should be stored as lowercase when changed in settings"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email().upper(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    user.refresh_from_db()
    assert payload["email"].lower() == user.email


def test_email_unique_iexact(client, user):
    """Email addresses should be unique for users when changed in settings
    even if different case"""
    other_user = factories.UserFactory()
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": other_user.email.upper(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    user.refresh_from_db()
    assert other_user.email != user.email
    assert other_user.email.upper() != user.email


def test_change_password_happy(client, user):
    """User can change their password."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "goodpass",
        "password1": "newpass123",
        "password2": "newpass123",
        "form_name": "password",
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
        "form_name": "password",
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
        "form_name": "password",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "You must type the same password each time" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="differentpass123") is False
    assert client.login(username=user.email, password="goodpass") is True
