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
