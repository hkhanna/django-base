import pytest
from playwright.sync_api import Page, expect
from django.urls import reverse
from . import factories


@pytest.fixture
def user(page: Page, live_server):
    user = factories.user_create()
    url = live_server.url + reverse("account_login")
    page.goto(url)
    page.get_by_label("E-mail").click()
    page.get_by_label("E-mail").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_label("Email")).to_have_value(user.email)
    return user


@pytest.fixture
def user_admin(page: Page, live_server):
    user = factories.user_create(is_staff=True, is_superuser=True)
    url = live_server.url + reverse("admin:index")
    page.goto(url)
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(user.email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("goodpass")
    page.get_by_role("button", name="Log in").click()
    return user


@pytest.mark.skip("")
def test_admin(page: Page, live_server, user_admin):
    """Existing user can log in."""
    url = live_server.url + reverse("admin:index")
    page.goto(url)
    expect(page.get_by_role("link", name="Events")).to_have_text("Events")


def test_settings(page: Page, live_server, user):
    """Existing user can log in."""
    url = live_server.url + reverse("account_settings")
    page.goto(url)
    expect(page.get_by_label("First name")).to_have_value(user.first_name)
