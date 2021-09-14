import pytest
from django.urls import reverse

from .. import models


@pytest.fixture
def password_reset_url(client, user):
    client.post(reverse("account_reset_password"), {"email": user.email}, follow=True)
    email_message = models.EmailMessage.objects.first()
    return email_message.template_context["password_reset_url"]


def test_reset_password(client, user, mailoutbox):
    """Launch a password reset email"""
    response = client.post(
        reverse("account_reset_password"), {"email": user.email}, follow=True
    )
    email_messages = models.EmailMessage.objects.all()

    assert response.status_code == 200
    assert "We have sent you a password reset email." in str(response.content)
    assert len(email_messages) == 1
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Password Reset Request"

    assert "http://" in mailoutbox[0].body
    assert "http://" in mailoutbox[0].alternatives[0][0]


def test_reset_password_key(client, password_reset_url):
    """Good uid, good token in url shows password reset form"""
    response = client.get(password_reset_url, follow=True)
    assert "Please choose a new password" in str(response.content)

    # The url forwards to the -set-password/ url.
    assert password_reset_url != response.request["PATH_INFO"]
    assert "set-password/" in response.request["PATH_INFO"]


def test_password_reset_confirm(client, user, password_reset_url):
    """Successfully change password"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"password1": "newpass123", "password2": "newpass123"}
    response = client.post(post_url, payload, follow=True)

    success = client.login(username=user.email, password="newpass123")
    assert success is True
    assert "Password successfully changed" in str(response.content)


def test_password_reset_confirm_bad_url(client, password_reset_url):
    """Bad url shows an error on the page and no form"""
    password_reset_url = (
        password_reset_url[:-5] + "bad" + password_reset_url[-3:]
    )  # Mess up the token

    response = client.get(password_reset_url, follow=True)

    assert "Bad Password Reset Token" in str(response.content)


def test_password_reset_confirm_twice(client, password_reset_url):
    """A reset password link used twice should not work"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"password1": "newpass123", "password2": "newpass123"}
    response = client.post(post_url, payload, follow=True)
    assert "Password successfully changed" in str(response.content)

    response = client.get(password_reset_url, follow=True)
    assert "Bad Password Reset Token" in str(response.content)


def test_password_reset_confirm_invalid(client, password_reset_url):
    """Passwords that don't pass validation should fail"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"password1": "bad", "password2": "bad"}
    response = client.post(post_url, payload, follow=True)
    assert "too short" in str(response.content)


def test_password_reset_confirm_mismatch(client, password_reset_url):
    """Mismatched passwords in confirmation return an error message from the form"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"password1": "goodpass123", "password2": "unmatched123"}
    response = client.post(post_url, payload, follow=True)
    assert "You must type the same password each time" in str(response.content)


def test_reset_inactive(client, user, mailoutbox):
    """An inactive account does not send a reset password email"""
    user.is_active = False
    user.save()
    response = client.post(
        reverse("account_reset_password"), {"email": user.email}, follow=True
    )
    assert response.status_code == 200
    assert len(mailoutbox) == 0
    assert "not assigned to any user account" in str(response.content)
