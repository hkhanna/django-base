import pytest
from waffle.testutils import override_switch
from django.urls import reverse

from .. import models


def test_signup_create(client):
    """Signing up creates the user"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    client.post(reverse("account_signup"), payload)
    assert 1 == models.User.objects.filter(email="harry@example.com").count()


def test_signup_login(client):
    """Signing up logs the user in"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload, follow=True)
    assert (
        response.wsgi_request.user
        == models.User.objects.filter(email="harry@example.com").first()
    )


def test_signup_weak_password(client):
    """Don't allow signup with a weak password"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password1": "the",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "common" in str(response.content)


def test_signup_duplicate(client, user):
    """Don't allow signup with an existing email address"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": user.email,
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "already registered" in str(response.content)


def test_signup_email_history(client):
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    client.post(reverse("account_signup"), payload)
    assert (
        models.User.objects.filter(email="harry@example.com").first().email_history[0]
        == "harry@example.com"
    )


def test_user_locked(client, user):
    """A locked user cannot sign up"""
    user.is_locked = True
    user.save()
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": user.email,
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "already registered" in str(response.content)


@override_switch("disable_signup", active=True)
def test_disable_user_creation(client):
    """Prevent user signups when disable_signup is True"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "Sign Up Closed" in str(response.content)
    assert 0 == models.User.objects.filter(email="harry@example.com").count()


def test_email_lowercase(client):
    """Email address should be stored as lowercase when signing up"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com".upper(),
        "password1": "a really good password!",
        "accept_terms": True,
    }
    client.post(reverse("account_signup"), payload)
    assert models.User.objects.filter(email="harry@example.com").exists() is True


def test_email_unique_iexact(client, user):
    """Email addresses should be unique for users when signing up even if different case"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": user.email.upper(),
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "A user is already registered with this e-mail address" in str(
        response.content
    )
    assert (
        models.User.objects.filter(email="harry@example.com".upper()).exists() is False
    )


def test_first_name_length(client, user):
    """First name must not exceed 150 characters"""
    payload = {
        "first_name": "A" * 151,
        "last_name": "Khanna",
        "email": "a@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "first_name" in response.context["form"].errors
    assert (
        "has at most 150 characters" in response.context["form"].errors["first_name"][0]
    )
    assert "has at most 150 characters" in str(response.content)


def test_last_name_length(client, user):
    """Last name must not exceed 150 characters"""
    payload = {
        "first_name": "Harry",
        "last_name": "A" * 151,
        "email": "a@example.com",
        "password1": "a really good password!",
        "accept_terms": True,
    }
    response = client.post(reverse("account_signup"), payload)
    assert "last_name" in response.context["form"].errors
    assert (
        "has at most 150 characters" in response.context["form"].errors["last_name"][0]
    )
    assert "has at most 150 characters" in str(response.content)
