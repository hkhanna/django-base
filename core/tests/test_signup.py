from django.urls import reverse

from .. import models, services, selectors, constants


def test_signup_create(client):
    """Signing up creates the user"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password": "a really good password!",
        "middle_initial": "",  # Honeypot
    }
    client.post(reverse("user:signup"), payload)
    assert 1 == selectors.user_list(email="harry@example.com").count()


def test_signup_login(client):
    """Signing up logs the user in"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload, follow=True)
    assert (
        response.wsgi_request.user
        == selectors.user_list(email="harry@example.com").first()
    )


def test_signup_weak_password(client):
    """Don't allow signup with a weak password"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password": "the",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "common" in str(response.content)


def test_signup_duplicate(client, user):
    """Don't allow signup with an existing email address"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": user.email,
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "already exists" in str(response.content)
    assert 1 == selectors.user_list().count()


def test_signup_email_history(client):
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password": "a really good password!",
    }
    client.post(reverse("user:signup"), payload)
    assert (
        selectors.user_list(email="harry@example.com").first().email_history[0]
        == "harry@example.com"
    )


def test_user_inactive(client, user):
    """An inactive user cannot sign up"""
    services.user_update(instance=user, is_active=False)
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": user.email,
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "already exists" in str(response.content)
    assert 1 == selectors.user_list().count()
    user.refresh_from_db()
    assert user.is_active is False  # Still inactive


def test_disable_user_creation(client):
    """Prevent user signups when disable_signup GlobalSetting is True"""
    services.global_setting_create(
        slug="disable_signup", type=constants.SettingType.BOOL, value="true"
    )
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com",
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "Sign up is closed." in str(response.content)
    assert 0 == services.user_list(email="harry@example.com").count()


def test_email_lowercase(client):
    """Email address should be stored as lowercase when signing up"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "harry@example.com".upper(),
        "password": "a really good password!",
    }
    client.post(reverse("user:signup"), payload)
    assert selectors.user_list(email="harry@example.com").exists() is True


def test_email_unique_iexact(client, user):
    """Email addresses should be unique for users when signing up even if different case"""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": user.email.upper(),
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "A user with that email already exists." in str(response.content)
    assert selectors.user_list(email="harry@example.com".upper()).exists() is False


def test_first_name_length(client, user):
    """First name must not exceed 150 characters"""
    payload = {
        "first_name": "A" * 151,
        "last_name": "Khanna",
        "email": "a@example.com",
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "has at most 150 characters" in str(response.content)


def test_last_name_length(client, user):
    """Last name must not exceed 150 characters"""
    payload = {
        "first_name": "Harry",
        "last_name": "A" * 151,
        "email": "a@example.com",
        "password": "a really good password!",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "has at most 150 characters" in str(response.content)


def test_honeypot(client):
    """If honeypot is provided, return 400."""
    payload = {
        "first_name": "Harry",
        "last_name": "Khanna",
        "email": "a@example.com",
        "password": "a really good password!",
        "middle_initial": "S",
    }
    response = client.post(reverse("user:signup"), payload)
    assert "Signup closed." in str(response.content)
    assert selectors.user_list().count() == 0
