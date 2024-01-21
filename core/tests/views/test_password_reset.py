import pytest
from django.urls import reverse

from ... import models, services


@pytest.fixture
def password_reset_url(client, user):
    client.post(reverse("user:password-reset"), {"email": user.email}, follow=True)
    email_message = models.EmailMessage.objects.first()
    return email_message.template_context["password_reset_url"]


def test_reset_password(client, user, mailoutbox):
    """Launch a password reset email"""
    response = client.post(reverse("user:password-reset"), {"email": user.email})
    email_messages = models.EmailMessage.objects.all()

    assert response.status_code == 302
    assert len(email_messages) == 1
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Password Reset Request"

    assert "http://" in mailoutbox[0].body
    assert "http://" in mailoutbox[0].alternatives[0][0]


def test_reset_password_key(client, password_reset_url):
    """Good uid, good token in url shows password reset form"""
    response = client.get(password_reset_url, follow=True)

    # The url forwards to the -set-password/ url.
    assert response.request["PATH_INFO"] not in password_reset_url
    assert "set-password/" in response.request["PATH_INFO"]


def test_password_reset_confirm(client, user, password_reset_url):
    """Successfully change password"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"new_password1": "newpass123", "new_password2": "newpass123"}
    response = client.post(post_url, payload, follow=True)
    assert response.wsgi_request.user.is_authenticated is True
    client.logout()

    success = client.login(username=user.email, password="newpass123")
    assert success is True


def test_password_reset_confirm_bad_url(client, password_reset_url):
    """Bad url shows does not redirect to the form"""
    password_reset_url = (
        password_reset_url[:-5] + "bad" + password_reset_url[-3:]
    )  # Mess up the token

    response = client.get(password_reset_url, follow=True)
    # No redirection happened to the form
    assert response.request["PATH_INFO"] in password_reset_url
    assert "set-password/" not in response.request["PATH_INFO"]


def test_password_reset_confirm_twice(client, password_reset_url):
    """A reset password link used twice should not work"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"new_password1": "newpass123", "new_password2": "newpass123"}
    response = client.post(post_url, payload)
    assert response.wsgi_request.user.is_authenticated is True
    client.logout()

    response = client.get(password_reset_url, follow=True)
    # No redirection happened to the form
    assert response.request["PATH_INFO"] in password_reset_url
    assert "set-password/" not in response.request["PATH_INFO"]


def test_password_reset_confirm_invalid(client, password_reset_url):
    """Passwords that don't pass validation should fail"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"new_password1": "bad", "new_password2": "bad"}
    response = client.post(post_url, payload, follow=True)
    assert "too short" in str(response.content)


def test_password_reset_confirm_mismatch(client, password_reset_url):
    """Mismatched passwords in confirmation return an error message from the form"""
    response = client.get(password_reset_url, follow=True)
    post_url = response.request["PATH_INFO"]
    payload = {"new_password1": "goodpass123", "new_password2": "unmatched123"}
    response = client.post(post_url, payload)
    assert "The two password fields" in str(response.content)


def test_reset_inactive(client, user, mailoutbox):
    """An inactive account does not send a reset password email"""
    services.user_update(instance=user, is_active=False)
    response = client.post(
        reverse("user:password-reset"), {"email": user.email}, follow=True
    )
    assert response.status_code == 200
    assert len(mailoutbox) == 0


def test_reset_email_no_reply_to(client, user, mailoutbox, settings):
    """Password reset email with no account_reply_to has no reply to"""
    settings.SITE_CONFIG["account_reply_to_name"] = None
    settings.SITE_CONFIG["account_reply_to_email"] = None

    client.post(reverse("user:password-reset"), {"email": user.email}, follow=True)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].reply_to == []


def test_reset_email_reply_to(client, user, mailoutbox, settings):
    """Password reset emails use the account_reply_to_email"""
    settings.SITE_CONFIG["account_reply_to_name"] = "Support"
    settings.SITE_CONFIG["account_reply_to_email"] = "support@example.com"

    client.post(reverse("user:password-reset"), {"email": user.email}, follow=True)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].reply_to == ["Support <support@example.com>"]


def test_reset_email_from(client, user, mailoutbox, settings):
    """Password reset emails use the account_from_email"""
    settings.SITE_CONFIG["account_from_name"] = "Support"
    settings.SITE_CONFIG["account_from_email"] = "support@example.com"
    settings.SITE_CONFIG[
        "default_from_name"
    ] = "Something Else"  # This should be ignored.
    settings.SITE_CONFIG[
        "default_from_email"
    ] = "somethingelse@example.com"  # This should be ignored.

    client.post(reverse("user:password-reset"), {"email": user.email}, follow=True)
    assert len(mailoutbox) == 1
    assert mailoutbox[0].from_email == "Support <support@example.com>"


def test_reset_password_unusable(client, user, mailoutbox):
    """Launch a password reset email even for users with an unusuable password"""
    user.set_unusable_password()
    user.save()
    response = client.post(reverse("user:password-reset"), {"email": user.email})
    email_messages = models.EmailMessage.objects.all()

    assert response.status_code == 302
    assert len(email_messages) == 1
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Password Reset Request"

    assert "http://" in mailoutbox[0].body
    assert "http://" in mailoutbox[0].alternatives[0][0]
