from urllib import request

import pytest
from django.conf import settings
from django.urls import reverse
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
def user(page: Page, live_server, settings):
    user = factories.user_create(is_staff=True, is_superuser=True)
    domain = live_server.url.split("://")[1]
    factories.org_create(
        owner=user, domain=domain
    )  # Create an org for the user in case other proejcts protect these views.
    url = live_server.url + reverse("user:login")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Sign in").click()
    expect(page).to_have_url(live_server.url + settings.LOGIN_REDIRECT_URL)
    return user


def test_login(page: Page, live_server):
    """User can login."""
    user = factories.user_create(is_staff=True, is_superuser=True)
    domain = live_server.url.split("://")[1]
    factories.org_create(
        owner=user, domain=domain
    )  # Create an org for the user in case other proejcts protect these views.
    url = live_server.url + reverse("user:login")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Sign in").click()
    expect(page).not_to_have_url(live_server.url + reverse("user:login"))
    expect(page).to_have_url(live_server.url + settings.LOGIN_REDIRECT_URL)


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

    expect(page).not_to_have_url(live_server.url + reverse("user:signup"))
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
    expect(page.get_by_label("Display name")).to_have_value(user.display_name)

    # Updates profile information
    page.get_by_label("First name").click()
    page.get_by_label("First name").fill("Example First")
    page.get_by_label("First name").press("Tab")
    page.get_by_label("Last name").fill("Example Last")
    page.get_by_label("Last name").press("Tab")
    page.get_by_label("Email").fill("new@example.com")
    page.get_by_label("Email").press("Tab")
    page.get_by_role("button", name="Update profile").click()
    expect(page.get_by_role("status").last).to_have_text("Profile updated.")
    user.refresh_from_db()
    assert user.first_name == "Example First"
    assert user.last_name == "Example Last"
    assert user.email == "new@example.com"

    # Normalize fields appropriately
    # Display name is still set to the old name
    assert user.display_name != "Example First" + " " + "Example Last"

    # Blank it out to regenerate it from the name on submit.
    page.get_by_label("Display name").fill("")
    page.get_by_role("button", name="Update profile").click()
    expect(page.get_by_label("Display name")).to_have_value(
        "Example First Example Last"
    )
    user.refresh_from_db()
    assert user.display_name == "Example First" + " " + "Example Last"

    # Put weird casing in the email to normalize it on submit.
    page.get_by_label("Email").fill("NEW@EXAMPLE.COM")
    page.get_by_role("button", name="Update profile").click()
    expect(page.get_by_label("Email")).to_have_value("new@example.com")
    user.refresh_from_db()
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
    expect(page.get_by_text("Password changed.")).not_to_be_visible()

    # Changes password, correct current password
    page.get_by_label("New password", exact=True).click()
    page.get_by_label("New password", exact=True).fill("newpass123")
    page.get_by_label("New password", exact=True).press("Tab")
    page.get_by_label("New password (again)").fill("newpass123")
    page.get_by_label("New password (again)").press("Tab")
    page.get_by_label("Current password", exact=True).fill("goodpass")
    page.get_by_label("Current password", exact=True).press("Enter")
    expect(page.get_by_role("status").last).to_have_text("Password changed.")
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


def test_terms_and_privacy(page: Page, live_server):
    """Terms of Use and Privacy Policy pages."""
    url = live_server.url + reverse("terms-of-use")
    page.goto(url)
    expect(page).to_have_url(url)
    expect(page.get_by_role("heading", level=1, name="Terms of Use")).to_be_visible()

    url = live_server.url + reverse("privacy-policy")
    page.goto(url)
    expect(page).to_have_url(url)
    expect(page.get_by_role("heading", level=1, name="Privacy Policy")).to_be_visible()
