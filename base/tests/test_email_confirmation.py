import pytest
from django.urls import reverse
import allauth.account.utils

from .. import models


@pytest.fixture
def user(client):
    """Create a user via the signup form to trigger all the allauth stuff."""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    client.post(reverse("account_signup"), payload)
    return models.User.objects.get(email="harry@example.com")


def test_user_create_confirm_email(user, mailoutbox):
    """Creating a user sends an email confirmation to the user"""
    assert user.emailaddress_set.first().verified is False
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Please Confirm Your E-Mail Address"


def test_user_create_confirm_email_success(client, user):
    """Clicking the appropriate link in the confirmation email will confirm a user's email address"""
    assert user.emailaddress_set.first().verified is False
    email_message = models.EmailMessage.objects.get(created_by=user)
    activate_url = email_message.template_context["activate_url"]
    client.get(activate_url, follow=True)
    user.refresh_from_db()
    assert user.emailaddress_set.first().verified is True


def test_user_create_confirm_email_twice(client, user):
    """A user email confirmation clicked twice should be idempotent."""
    assert user.emailaddress_set.first().verified is False
    email_message = models.EmailMessage.objects.get(created_by=user)
    activate_url = email_message.template_context["activate_url"]
    response = client.get(activate_url, follow=True)

    # When not logged in, it redirects to login page with this message.
    assert "You have confirmed" in str(response.content)
    user.refresh_from_db()
    assert user.emailaddress_set.first().verified is True
    response = client.get(activate_url, follow=True)
    assert "You have confirmed" in str(response.content)
    assert user.emailaddress_set.first().verified is True


def test_user_create_confirm_email_bad_token(client, user):
    """A bad token should not confirm a user's email"""
    assert user.emailaddress_set.first().verified is False
    email_message = models.EmailMessage.objects.get(created_by=user)
    activate_url = email_message.template_context["activate_url"]

    # Remove one letter from the key
    activate_url = activate_url[:-4] + activate_url[-5:]

    response = client.get(activate_url, follow=True)
    user.refresh_from_db()
    assert user.emailaddress_set.first().verified is False
    assert "expired or is invalid" in str(response.content)
