import freezegun
from datetime import timedelta
import pytest
from playwright.sync_api import Page, expect
from django.urls import reverse
from django.utils import timezone
from . import factories
from .. import selectors


@pytest.fixture
def user(page: Page, live_server):
    user = factories.user_create(is_staff=True, is_superuser=True)
    url = live_server.url + reverse("account_login")
    page.goto(url)
    page.get_by_label("E-mail").click()
    page.get_by_label("E-mail").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_label("Email")).to_have_value(user.email)
    return user


def test_settings(page: Page, live_server, user):
    """User can update their information on the settings page."""
    url = live_server.url + reverse("account_settings")
    page.goto(url)
    expect(page.get_by_label("First name")).to_have_value(user.first_name)
    expect(page.get_by_label("Last name")).to_have_value(user.last_name)
    expect(page.get_by_label("Email")).to_have_value(user.email)

    # Updates personal information but use the wrong password
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Example First")
    page.get_by_label("First name").press("Tab")
    page.get_by_label("Last name").fill("Example Last")
    page.get_by_label("Last name").press("Tab")
    page.get_by_label("Email").fill("new@example.com")
    page.get_by_label("Email").press("Tab")
    page.get_by_placeholder("Current password", exact=True).fill("badpass")
    page.get_by_placeholder("Current password", exact=True).press("Enter")
    expect(page.get_by_text("Please type your current password.")).to_be_visible()
    user.refresh_from_db()
    assert user.first_name != "Example First"
    assert user.last_name != "Example Last"
    assert user.email != "new@example.com"

    # Corrects password and personal information is updated
    page.get_by_placeholder("Current password", exact=True).click()
    page.get_by_placeholder("Current password", exact=True).fill("goodpass")
    page.get_by_placeholder("Current password", exact=True).press("Enter")
    expect(page.get_by_text("Personal information saved")).to_be_visible()
    user.refresh_from_db()
    assert user.first_name == "Example First"
    assert user.last_name == "Example Last"
    assert user.email == "new@example.com"

    # Changes password, wrong current password
    page.get_by_placeholder("New Password", exact=True).click()
    page.get_by_placeholder("New Password", exact=True).fill("newpass123")
    page.get_by_placeholder("New Password", exact=True).press("Tab")
    page.get_by_placeholder("New Password (again)").fill("newpass123")
    page.get_by_placeholder("New Password (again)").press("Tab")
    page.get_by_placeholder("Current Password", exact=True).fill("badpass")
    page.get_by_placeholder("Current Password", exact=True).press("Enter")
    expect(page.get_by_text("Please type your current password.")).to_be_visible()
    expect(page.get_by_text("Password successfully changed")).not_to_be_visible()

    # Changes password, correct current password
    page.get_by_placeholder("New Password", exact=True).click()
    page.get_by_placeholder("New Password", exact=True).fill("newpass123")
    page.get_by_placeholder("New Password", exact=True).press("Tab")
    page.get_by_placeholder("New Password (again)").fill("newpass123")
    page.get_by_placeholder("New Password (again)").press("Tab")
    page.get_by_placeholder("Current Password", exact=True).fill("goodpass")
    page.get_by_placeholder("Current Password", exact=True).press("Enter")
    expect(page.get_by_text("Password successfully changed")).to_be_visible()
    user.refresh_from_db()
    assert user.check_password("newpass123") is True

    # Log out
    page.get_by_role("button", name="Open user menu").click()
    page.get_by_role("menuitem", name="Sign out").click()
    page.wait_for_url(live_server.url + reverse("account_login"))
    assert page.url == live_server.url + reverse("account_login")


def test_organizations(page: Page, live_server, user):
    """Organization views"""

    with freezegun.freeze_time(timezone.now() - timedelta(days=1)):
        org = factories.org_create(owner=user)
    url = live_server.url + reverse("account_settings")
    page.goto(url)

    # Initially on the personal org
    expect(page.get_by_role("button", name=f"Open user menu")).to_contain_text(
        user.name
    )

    # Switch to the new org
    page.get_by_role("button", name="Open user menu").click()
    page.get_by_role("menuitem", name=org.name).click()

    # Access the org's settings
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


@pytest.mark.skip("not implemented")
def test_signup(page: Page, live_server):
    """Signup and confirm email"""


@pytest.mark.skip("not implemented")
def test_email_confirmation(page: Page, live_server):
    """Email confirmation (including resend)"""


@pytest.mark.skip("not implemented")
def test_password_reset(page: Page, live_server):
    """Password reset"""


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
    expect(page.get_by_role("link", name="Events")).to_have_text("Events")
