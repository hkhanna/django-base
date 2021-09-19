from django.urls import reverse
from django.conf import settings


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
    response = client.get(reverse("account_logout"), follow=True)
    assert "signed out" in str(response.content)
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert "signed out" in str(messages[0])
