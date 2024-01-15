from django.urls import reverse
from django.conf import settings
from freezegun import freeze_time
from core import services


def test_login(client, user):
    """Successfully login"""
    response = client.post(
        reverse("user:login"), {"username": user.email, "password": "goodpass"}
    )
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL


def test_login_iexact(client, user):
    """Email address is case insensitive."""
    response = client.post(
        reverse("user:login"), {"username": user.email.upper(), "password": "goodpass"}
    )
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL


def test_login_bad(client, user):
    response = client.post(
        reverse("user:login"), {"username": user.email, "password": "badpass"}
    )
    assert "Please enter a correct email address and password." in str(response.content)


def test_login_inactive(client, user):
    """Inactive user should present as no user in the system"""
    services.user_update(instance=user, is_active=False)
    response = client.post(
        reverse("user:login"), {"username": user.email, "password": "goodpass"}
    )
    assert "Please enter a correct email address and password." in str(response.content)


def test_logout(client, user):
    client.force_login(user)
    response = client.post(reverse("user:logout"))
    assert response.status_code == 302
    assert response.url == reverse("user:login")
    assert response.wsgi_request.user.is_authenticated is False


def test_login_detected_tz(client, user):
    """Logging in with a detected_tz stores it in the user's session"""
    client.post(
        reverse("user:login"),
        {
            "username": user.email,
            "password": "goodpass",
            "detected_tz": "America/New_York",
        },
    )

    response = client.get(reverse("user:profile"))
    session = response.wsgi_request.session
    assert session["detected_tz"] == "America/New_York"


def test_login_no_user(client):
    """If email address doesn't exist, it should disallow login."""
    response = client.post(
        reverse("user:login"),
        {"username": "bademail@example.com", "password": "badpass"},
    )
    assert "Please enter a correct email address and password." in str(response.content)


def test_login_weird_email(client):
    """If email address is malformed in a certain way, it should not error."""
    response = client.post(
        reverse("user:login"),
        {"username": "2@3.4", "password": "badpass"},
    )
    assert "Please enter a correct email address and password." in str(response.content)


def test_session_length(client, user):
    """Session should last for the expected amount of time."""
    expected_session_length = 15_552_000  # 180 days

    with freeze_time("2022-11-04 12:00:00Z") as frozen_dt:
        response = client.post(
            reverse("user:login"), {"username": user.email, "password": "goodpass"}
        )
        response = client.get(reverse("user:profile"))
        assert response.wsgi_request.user.is_authenticated is True
        assert response.status_code == 200

        # Still logged in with 1 second to go
        # Accessing extends the session expiry because we modify the session.
        frozen_dt.tick(delta=expected_session_length - 1)
        response = client.get(reverse("user:profile"))
        assert response.wsgi_request.user.is_authenticated is True
        assert response.status_code == 200

        # Session expired
        frozen_dt.tick(delta=expected_session_length)
        response = client.get(reverse("user:profile"))
        assert response.wsgi_request.user.is_authenticated is False
        assert response.status_code == 302
