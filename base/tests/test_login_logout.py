from django.urls import reverse
from django.conf import settings
from freezegun import freeze_time


def test_login_happy(client, user):
    """Successfully login"""
    response = client.post(
        reverse("account_login"), {"login": user.email, "password": "goodpass"}
    )
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL


def test_login_iexact(client, user):
    """Email address is case insensitive."""
    response = client.post(
        reverse("account_login"), {"login": user.email.upper(), "password": "goodpass"}
    )
    assert response.status_code == 302
    assert response.url == settings.LOGIN_REDIRECT_URL


def test_login_bad(client, user):
    response = client.post(
        reverse("account_login"), {"login": user.email, "password": "badpass"}
    )
    assert "e-mail address and/or password you specified are not correct" in str(
        response.content
    )


def test_login_inactive(client, user):
    """Inactive user should present as no user in the system"""
    user.is_active = False
    user.save()
    response = client.post(
        reverse("account_login"), {"login": user.email, "password": "goodpass"}
    )
    assert "e-mail address and/or password you specified are not correct" in str(
        response.content
    )


def test_locked_login(client, user):
    """Locked (inactive) user should get a 400 error when trying to log in."""
    user.is_locked = True
    user.save()
    response = client.post(
        reverse("account_login"), {"login": user.email, "password": "goodpass"}
    )
    assert "has been locked" in str(response.content)


def test_logout(client, user):
    client.force_login(user)
    response = client.get(reverse("account_logout"))
    assert "Sign Out" in str(response.content)
    messages = list(response.context["messages"])
    assert len(messages) == 0

    response = client.post(reverse("account_logout"), follow=True)
    assert "signed out" in str(response.content)
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert "signed out" in str(messages[0])


def test_login_detected_tz(client, user):
    """Logging in with a detected_tz stores it in the user's session"""
    client.post(
        reverse("account_login"),
        {
            "login": user.email,
            "password": "goodpass",
            "detected_tz": "America/New_York",
        },
    )

    response = client.get(reverse("account_settings"))
    session = response.wsgi_request.session
    assert session["detected_tz"] == "America/New_York"


def test_login_no_user(client):
    """If email address doesn't exist, it should disallow login."""
    response = client.post(
        reverse("account_login"),
        {"login": "bademail@example.com", "password": "badpass"},
    )
    assert "e-mail address and/or password you specified are not correct" in str(
        response.content
    )


def test_login_weird_email(client):
    """If email address is malformed in a certain way, it should not error."""
    response = client.post(
        reverse("account_login"),
        {"login": "2@3.4", "password": "badpass"},
    )
    assert "Enter a valid email address." in str(response.content)


def test_session_length(client, user):
    """Session should last for the expected amount of time."""
    expected_session_length = 15_552_000  # 180 days

    with freeze_time("2022-11-04 12:00:00Z") as frozen_dt:
        response = client.post(
            reverse("account_login"), {"login": user.email, "password": "goodpass"}
        )
        response = client.get(reverse("account_settings"))
        assert response.wsgi_request.user.is_authenticated is True
        assert response.status_code == 200

        # Still logged in with 1 second to go
        # Accessing extends the session expiry because we modify the session.
        frozen_dt.tick(delta=expected_session_length - 1)
        response = client.get(reverse("account_settings"))
        assert response.wsgi_request.user.is_authenticated is True
        assert response.status_code == 200

        # Session expired
        frozen_dt.tick(delta=expected_session_length)
        response = client.get(reverse("account_settings"))
        assert response.wsgi_request.user.is_authenticated is False
        assert response.status_code == 302
