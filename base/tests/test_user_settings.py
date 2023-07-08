from django.urls import reverse
from allauth.account import models as auth_models
from allauth.socialaccount import models as socialauth_models

from .. import models, factories


def test_get_settings(client, user):
    """Settings page should contain the user's information."""
    client.force_login(user)
    response = client.get(reverse("account_settings"))
    assert user.first_name in str(response.content)
    assert user.last_name in str(response.content)
    assert user.email in str(response.content)


def test_change_info(client, user):
    """User can change their personal info"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    response = client.post(reverse("account_settings"), payload, follow=True)
    assert "Personal information saved" in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] == user.first_name
    assert payload["last_name"] == user.last_name
    assert payload["email"] == user.email
    assert len(user.email_history) == 2


def test_change_info_bad(client, user):
    """User must provide their current password to change their personal info"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "badpass",
        "form_name": "pi",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "type your current password" in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] != user.first_name
    assert payload["last_name"] != user.last_name
    assert payload["email"] != user.email


def test_change_email_sync(client, user):
    """A changed User email address should keep EmailAddress in sync with User.email"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    email_address = auth_models.EmailAddress.objects.get(user=user)
    assert email_address.email == payload["email"]


def test_change_email_confirm(client, user, mailoutbox):
    """A changed User email address should send a confirmation email"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    email_message = models.EmailMessage.objects.filter(created_by=user).first()
    assert email_message.to_email == payload["email"]
    assert "Confirm Your E-Mail" in mailoutbox[0].subject


def test_no_email_change(client, user):
    """A personal information update that does not update the user's email
    (case insensitive) should not send a confirmation email and doesn't
    add to the email history."""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": user.email.upper(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    assert models.EmailMessage.objects.filter(created_by=user).exists() is False
    user.refresh_from_db()
    assert len(user.email_history) == 1
    assert user.email_history[0] == user.email


def test_email_lowercase(client, user):
    """Email address should be stored as lowercase when changed in settings"""
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": factories.fake.safe_email().upper(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    user.refresh_from_db()
    assert payload["email"].lower() == user.email


def test_email_unique_iexact(client, user):
    """Email addresses should be unique for users when changed in settings
    even if different case"""
    other_user = factories.UserFactory()
    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": other_user.email.upper(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    user.refresh_from_db()
    assert other_user.email != user.email
    assert other_user.email.upper() != user.email


def test_resend_email_confirmation(client, user, mailoutbox):
    """User may request another email confirmation"""
    # Unverify email first
    email_address = user.emailaddress_set.first()
    email_address.verified = False
    email_address.save()

    client.force_login(user)
    assert models.EmailMessage.objects.count() == 0
    response = client.post(reverse("account_resend_confirmation_email"))
    assert response.status_code == 302
    assert response.url == reverse("account_settings")
    assert models.EmailMessage.objects.count() == 1
    email = models.EmailMessage.objects.first()
    assert email.created_by == user
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "Please Confirm Your E-Mail Address"


def test_change_password_happy(client, user):
    """User can change their password."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "goodpass",
        "password1": "newpass123",
        "password2": "newpass123",
        "form_name": "password",
    }
    response = client.post(reverse("account_settings"), payload, follow=True)
    assert "Password successfully changed" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is True
    assert client.login(username=user.email, password="goodpass") is False


def test_change_password_incorrect(client, user):
    """User must provide their current password to change it."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "bad",
        "password1": "newpass123",
        "password2": "newpass123",
        "form_name": "password",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "type your current password" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="goodpass") is True


def test_change_password_match(client, user):
    """User's new passwords must match to change them."""
    client.login(username=user.email, password="goodpass")
    payload = {
        "oldpassword": "goodpass",
        "password1": "newpass123",
        "password2": "differentpass123",
        "form_name": "password",
    }
    response = client.post(reverse("account_settings"), payload)
    assert "You must type the same password each time" in str(response.content)
    assert client.login(username=user.email, password="newpass123") is False
    assert client.login(username=user.email, password="differentpass123") is False
    assert client.login(username=user.email, password="goodpass") is True


def test_user_delete(client, user):
    """Deleting a user should disable User.is_active"""
    assert client.login(username=user.email, password="goodpass") is True

    response = client.post(reverse("account_delete"), follow=True)
    assert "has been deleted" in str(response.content)
    user.refresh_from_db()

    assert client.login(username=user.email, password="goodpass") is False
    assert user.is_active is False


def test_user_create_after_delete(client, user):
    """Deleted user signing up again should re-enable is_active"""
    assert client.login(username=user.email, password="goodpass") is True
    response = client.post(reverse("account_delete"))
    user.refresh_from_db()
    assert user.is_active is False

    payload = {
        "first_name": "New",
        "last_name": "Name",
        "email": user.email,
        "password1": "a really good password!",
    }
    response = client.post(reverse("account_signup"), payload, follow=True)
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_active is True
    assert user.first_name == "New"
    assert user.last_name == "Name"


def test_deleted_user_access(client, user):
    """If User.is_active is False, user cannot access logged in endpoints"""
    client.force_login(user)
    response = client.get(reverse("account_settings"))
    user.is_active = False
    user.save()
    response = client.get(reverse("account_settings"))
    assert response.status_code == 302


def test_deleted_user_unconfirm_email(client, user):
    """A User with a confirmed email address that gets deleted automatically unconfirms their email.
    This is useful in case they sign up again."""
    client.force_login(user)
    email_address = auth_models.EmailAddress.objects.get(user=user)
    email_address.verified = True
    email_address.save()
    client.post(reverse("account_delete"))
    email_address.refresh_from_db()
    assert email_address.verified is False


def test_deleted_user_unconfirm_email_social(client, user):
    """Deleting a user deletes all connected SocialAccounts."""
    other_user = factories.UserFactory()
    socialauth_models.SocialAccount.objects.create(
        user=user, provider="Google", uid="123"
    )
    socialauth_models.SocialAccount.objects.create(
        user=other_user, provider="Google", uid="456"
    )
    assert other_user.socialaccount_set.count() == 1
    assert user.socialaccount_set.count() == 1

    client.force_login(user)
    client.post(reverse("account_delete"))

    assert user.socialaccount_set.count() == 0

    # Other user is not touched
    assert other_user.socialaccount_set.count() == 1


def test_change_email_to_deleted_user(client, user):
    """Edge case: user attempts to change their email address to the email address
    of a deleted user. It should succeed and change the deleted user's email address."""
    email = "harry@example.com"
    deleted_user = factories.UserFactory(is_active=False, email=email)

    client.force_login(user)
    payload = {
        "first_name": factories.fake.first_name(),
        "last_name": factories.fake.last_name(),
        "email": email,
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    client.post(reverse("account_settings"), payload)
    user.refresh_from_db()
    deleted_user.refresh_from_db()
    assert user.email == email
    assert deleted_user.email == f"harry+{deleted_user.pk}@example.com"


def test_name_length(client, user):
    """First and last name each must not exceed 150 characters"""
    client.force_login(user)
    payload = {
        "first_name": "A" * 151,
        "last_name": "B" * 151,
        "email": factories.fake.safe_email(),
        "oldpassword": "goodpass",
        "form_name": "pi",
    }
    response = client.post(reverse("account_settings"), payload, follow=True)
    assert "first_name" in response.context["pi_form"].errors
    assert "last_name" in response.context["pi_form"].errors
    assert (
        "has at most 150 characters"
        in response.context["pi_form"].errors["first_name"][0]
    )
    assert (
        "has at most 150 characters"
        in response.context["pi_form"].errors["last_name"][0]
    )
    assert str(response.content).count("has at most 150 characters") == 2
    assert "Personal information saved" not in str(response.content)
    user.refresh_from_db()
    assert payload["first_name"] != user.first_name
    assert payload["last_name"] != user.last_name
    assert payload["email"] != user.email
    assert len(user.email_history) == 1
    assert response.wsgi_request.user.first_name != "A" * 151
    assert response.wsgi_request.user.last_name != "B" * 151
