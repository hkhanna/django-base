from django.urls import reverse

from .. import factories


def test_change_password_happy(client, user):
    """User can change their password."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "old_password": "goodpass",
        "new_password1": "newpass123",
        "new_password2": "newpass123",
    }
    response = client.post(reverse("user:password-change"), payload, follow=True)
    assert client.login(username=user.email, password="newpass123") is True
    assert client.login(username=user.email, password="goodpass") is False
    assert "Password changed." in str(response.content)


def test_change_password_incorrect(client, user):
    """User must provide their current password to change it."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "old_password": "bad",
        "new_password1": "newpass123",
        "new_password2": "newpass123",
    }
    response = client.post(reverse("user:password-change"), payload)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="goodpass") is True
    assert "Your old password was entered incorrectly. Please enter it again." in str(
        response.content
    )


def test_change_password_match(client, user):
    """User's new passwords must match to change them."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "old_password": "goodpass",
        "new_password1": "newpass123",
        "new_password2": "differentpass123",
    }
    response = client.post(reverse("user:password-change"), payload)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="differentpass123") is False
    assert client.login(username=user.email, password="goodpass") is True
    assert "The two password fields" in str(response.content)


def test_change_password_unset(client, user):
    """User without a password can set it."""
    # User has a password
    client.force_login(user)

    payload = {
        "new_password1": "newpass123",
        "new_password2": "newpass123",
    }
    response = client.post(reverse("user:password-change"), payload)
    assert "This field is required." in str(response.content)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="goodpass") is True

    # Now, remove the user's password.
    user.set_unusable_password()
    user.save()
    client.force_login(user)

    payload = {
        "new_password1": "newpass123",
        "new_password2": "newpass123",
    }
    response = client.post(reverse("user:password-change"), payload, follow=True)
    assert client.login(username=user.email, password="newpass123") is True
    assert client.login(username=user.email, password="goodpass") is False
