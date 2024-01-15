from django.urls import reverse

from .. import factories


def test_get_profile(client, user):
    """Profile page should contain the user's information."""
    client.force_login(user)
    response = client.get(reverse("user:profile"))
    assert user.first_name in str(response.content)
    assert user.last_name in str(response.content)
    assert user.email in str(response.content)


def test_no_change(client, user):
    """User should be able to submit no changes."""
    # This is a regression test for a bug where the user's email would be
    # flagged as a duplicate if they didn't change it.
    client.force_login(user)
    payload = {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }
    response = client.post(reverse("user:profile"), payload, follow=True)
    assert "Profile updated." in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] == user.first_name
    assert payload["last_name"] == user.last_name
    assert payload["email"] == user.email
    assert len(user.email_history) == 1


def test_change_info(client, user):
    """User can change their personal info"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
    }
    response = client.post(reverse("user:profile"), payload, follow=True)
    assert "Profile updated." in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] == user.first_name
    assert payload["last_name"] == user.last_name
    assert payload["email"] == user.email
    assert len(user.email_history) == 2


def test_email_lowercase(client, user):
    """Email address should be stored as lowercase when changed in the profile."""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email().upper(),
    }
    client.post(reverse("user:profile"), payload)
    user.refresh_from_db()
    assert payload["email"].lower() == user.email


def test_email_unique_iexact(client, user):
    """Email addresses should be unique for users when changed in settings
    even if different case"""
    other_user = factories.user_create()
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": other_user.email.upper(),
    }
    client.post(reverse("user:profile"), payload)
    user.refresh_from_db()
    assert other_user.email != user.email
    assert other_user.email.upper() != user.email


def test_inactive_user_access(client, user):
    """If User.is_active is False, user cannot access logged in endpoints"""
    client.force_login(user)
    response = client.get(reverse("user:profile"))
    user.is_active = False
    user.save()
    response = client.get(reverse("user:profile"))
    assert response.status_code == 302


def test_name_length(client, user):
    """First and last name each must not exceed 150 characters"""
    client.force_login(user)
    payload = {
        "first_name": "A" * 151,
        "last_name": "B" * 151,
        "email": factories.fake.safe_email(),
    }
    response = client.post(reverse("user:profile"), payload, follow=True)
    assert str(response.content).count("has at most 150 characters") == 2
    assert "Profile updated." not in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] != user.first_name
    assert payload["last_name"] != user.last_name
    assert payload["email"] != user.email
    assert len(user.email_history) == 1
    assert response.wsgi_request.user.first_name != "A" * 151
    assert response.wsgi_request.user.last_name != "B" * 151
