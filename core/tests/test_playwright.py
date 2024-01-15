from datetime import timedelta
from urllib import request

import freezegun
import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import Page, expect

from .. import selectors
from . import factories


def vite_not_running():
    """Ensures the vite server is running."""
    # Really only needed for playwright tests.
    try:
        request.urlopen(
            "http://localhost:"
            + str(settings.DJANGO_VITE["default"].get("dev_server_port")),
            timeout=1,
        )
    except request.URLError as e:
        if not isinstance(e, request.HTTPError):
            return True
    return False


pytestmark = pytest.mark.skipif(
    vite_not_running(),
    reason="Vite server must be running on "
    + str(settings.DJANGO_VITE["default"].get("dev_server_port")),
)


@pytest.fixture
def user(page: Page, live_server):
    user = factories.user_create(is_staff=True, is_superuser=True)
    url = live_server.url + reverse("user:login")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Sign in").click()
    expect(page).to_have_url(live_server.url + reverse("user:profile"))
    expect(page.get_by_label("Email")).to_have_value(user.email)
    return user


def test_login(page: Page, live_server):
    """User can login."""
    user = factories.user_create(is_staff=True, is_superuser=True)
    url = live_server.url + reverse("user:login")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Sign in").click()
    expect(page).to_have_url(live_server.url + reverse("user:profile"))
    expect(page.get_by_label("Email")).to_have_value(user.email)


def test_signup(page: Page, live_server):
    """User can signup"""
    url = live_server.url + reverse("user:signup")
    page.goto(url)

    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Example First")
    page.get_by_label("First name").press("Tab")
    page.get_by_label("Last name").fill("Example Last")
    page.get_by_label("Last name").press("Tab")
    page.get_by_label("Email").fill("new@example.com")
    page.get_by_label("Email").press("Tab")
    page.get_by_label("Password").fill("new@example.com")
    page.get_by_role("button", name="Create account").click()

    expect(page).to_have_url(live_server.url + reverse("user:profile"))
    user = selectors.user_list(email="new@example.com").get()
    assert user.first_name == "Example First"
    assert user.last_name == "Example Last"
    assert user.email == "new@example.com"


def test_profile(page: Page, live_server, user):
    """User can update their profile information."""
    url = live_server.url + reverse("user:profile")
    page.goto(url)
    expect(page.get_by_label("Email")).to_have_value(user.email)
    expect(page.get_by_label("First name")).to_have_value(user.first_name)
    expect(page.get_by_label("Last name")).to_have_value(user.last_name)

    # Updates profile information
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Example First")
    page.get_by_label("First name").press("Tab")
    page.get_by_label("Last name").fill("Example Last")
    page.get_by_label("Last name").press("Tab")
    page.get_by_label("Email").fill("new@example.com")
    page.get_by_label("Email").press("Tab")
    page.get_by_role("button", name="Update profile").click()
    expect(page.get_by_role("region", name="Notifications (F8)")).to_have_text(
        "Profile updated."
    )
    user.refresh_from_db()
    assert user.first_name == "Example First"
    assert user.last_name == "Example Last"
    assert user.email == "new@example.com"


def test_change_password(page: Page, live_server, user):
    """User can update their password."""
    url = live_server.url + reverse("user:password-change")
    page.goto(url)
    expect(page.get_by_label("New password", exact=True)).to_be_editable()
    expect(page.get_by_label("New password (again)")).to_be_editable()
    expect(page.get_by_label("Current password")).to_be_editable()

    # Changes password, wrong current password
    page.get_by_label("New password", exact=True).click()
    page.get_by_label("New password", exact=True).fill("newpass123")
    page.get_by_label("New password", exact=True).press("Tab")
    page.get_by_label("New password (again)").fill("newpass123")
    page.get_by_label("New password (again)").press("Tab")
    page.get_by_label("Current password", exact=True).fill("badpass")
    page.get_by_label("Current password", exact=True).press("Enter")
    expect(
        page.get_by_text("Your old password was entered incorrectly.")
    ).to_be_visible()
    expect(page.get_by_text("Account updated.")).not_to_be_visible()

    # Changes password, correct current password
    page.get_by_label("New password", exact=True).click()
    page.get_by_label("New password", exact=True).fill("newpass123")
    page.get_by_label("New password", exact=True).press("Tab")
    page.get_by_label("New password (again)").fill("newpass123")
    page.get_by_label("New password (again)").press("Tab")
    page.get_by_label("Current password", exact=True).fill("goodpass")
    page.get_by_label("Current password", exact=True).press("Enter")
    expect(page.get_by_role("region", name="Notifications (F8)")).to_have_text(
        "Account updated."
    )
    user.refresh_from_db()
    assert user.check_password("newpass123") is True


def test_password_reset(page: Page, live_server, mailoutbox):
    """User can reset their password."""
    user = factories.user_create()
    url = live_server.url + reverse("user:password-reset")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_role("button", name="Send password reset email").click()
    expect(
        page.get_by_role("button", name="Send password reset email")
    ).not_to_be_visible()

    email_message = selectors.email_message_list().get()
    assert email_message.template_prefix == "core/email/password_reset"
    assert email_message.to_email == user.email
    assert len(mailoutbox) == 1


def test_organizations(page: Page, live_server, user):
    """Organization views"""

    with freezegun.freeze_time(timezone.now() - timedelta(days=1)):
        org = factories.org_create(owner=user)
    url = live_server.url + reverse("org_detail")
    page.goto(url)

    # Initially on the personal org
    expect(page.get_by_role("button", name=f"Open user menu")).to_contain_text(
        user.name
    )

    # Switch to the new org
    page.get_by_role("button", name="Open user menu").click()
    page.get_by_role("menuitem", name=org.name).click()

    # Access the org's settings
    page.goto(url)
    page.get_by_role("link", name="Organization Settings").click()

    # Invite a new member
    new_email = factories.fake.email(safe=True)
    page.get_by_role("button", name="Invite a Member").click()
    page.get_by_label("Email Address").click()
    page.get_by_label("Email Address").fill(new_email)
    page.get_by_text("Invite", exact=True).click()
    expect(page.get_by_text("has been invited to " + org.name)).to_be_visible()
    assert selectors.org_invitation_list(email=new_email).count() == 1
    assert selectors.email_message_list(to_email=new_email).count() == 1

    # Re-send invitation
    page.get_by_role("button", name="Resend").click()
    page.get_by_text("Confirm Resend").click()
    assert selectors.org_invitation_list(email=new_email).count() == 1
    assert selectors.email_message_list(to_email=new_email).count() == 2

    # Cancel invitation
    page.get_by_role("button", name="Cancel").click()
    page.get_by_text("Confirm Cancel").click()
    assert selectors.org_invitation_list(email=new_email).count() == 0


def test_admin(page: Page, live_server):
    """Admin user can log in."""
    user = factories.user_create(is_staff=True, is_superuser=True)
    url = live_server.url + reverse("admin:index")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Log in").click()

    url = live_server.url + reverse("admin:index")
    page.goto(url)
    expect(page.get_by_role("link", name="Administration")).to_contain_text(
        f"Administration ({settings.ENVIRONMENT})"
    )
