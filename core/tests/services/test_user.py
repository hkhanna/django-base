import pytest
from pytest_django.asserts import assertRaisesMessage
from unittest.mock import MagicMock
from django.urls import reverse
from core import services, selectors, constants
from core.exceptions import *


@pytest.fixture
def req(rf):
    req = rf.get("/")
    req.session = MagicMock()
    req.user = MagicMock()
    return req


@pytest.fixture(autouse=True)
def google_api_mock(monkeypatch):
    """Mock the requests module for Google REST API calls"""

    class MockResponse:
        responses = {
            "access_token": {"access_token": "test_access_token"},
            "user_info": {
                "given_name": "John",
                "family_name": "Doe",
                "name": "John Doe",
                "email": "john@example.com",
            },
        }

        def __init__(self, url, *args, **kwargs):
            if "https://oauth2.googleapis.com/token" in url:
                self.request_type = "access_token"
            elif "https://www.googleapis.com/oauth2/v2/userinfo" in url:
                self.request_type = "user_info"
            else:
                raise ValueError("Invalid URL")

        def json(self):
            return self.responses[self.request_type]

    monkeypatch.setattr("requests.post", MockResponse)
    monkeypatch.setattr("requests.get", MockResponse)
    return MockResponse


def test_google_oauth_attempt_login(req, user, google_api_mock):
    """Attempt to log in with Google OAuth if the user exists"""
    user_info = {
        "given_name": user.first_name,
        "family_name": user.last_name,
        "name": user.display_name,
        "email": user.email,
    }
    google_api_mock.responses["user_info"] = user_info
    oauth_service = services.GoogleOAuthService(request=req, view="login")
    user_, user_info_ = oauth_service.attempt_login(request=req, code="test")
    assert user == user_
    assert user_info == user_info_
    assert req.user == user


def test_google_oauth_attempt_login_nouser(req):
    """Attempt to log in with Google OAuth if the user does not exist"""
    oauth_service = services.GoogleOAuthService(request=req, view="login")
    user, user_info = oauth_service.attempt_login(request=req, code="test")
    assert user is None
    assert user_info["email"] == "john@example.com"


def test_google_oauth_signup_from_user_info(req):
    """This test verifies that the `signup_from_user_info` method of the GoogleOAuthService class correctly creates a new user
    based on the user information retrieved from the Google OAuth service."""
    oauth_service = services.GoogleOAuthService(request=req, view="login")
    user, user_info = oauth_service.attempt_login(request=req, code="test")
    assert user is None
    user = oauth_service.signup_from_user_info(user_info)
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.email == "john@example.com"


def test_google_oauth_signup_disabled(req):
    services.global_setting_create(
        slug="disable_signup", type=constants.SettingType.BOOL, value="true"
    )
    oauth_service = services.GoogleOAuthService(request=req, view="login")
    user, user_info = oauth_service.attempt_login(request=req, code="test")
    assert user is None

    with assertRaisesMessage(ApplicationError, "User signup is disabled."):
        user = oauth_service.signup_from_user_info(user_info)

    assert 0 == selectors.user_list(email="harry@example.com").count()
