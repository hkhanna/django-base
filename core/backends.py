from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.urls import reverse
import requests

from . import selectors

User = get_user_model()


# Inspired by https://aurigait.com/blog/google-oauth-integration-in-django-without-utilizing-django-allauth/
class GoogleAuthBackend(BaseBackend):
    """Custom Backend Server for Google auth"""

    def _get_access_token(self, request, code):
        """Return access_token from code"""

        redirect_uri = request.build_absolute_uri(reverse("user:google-callback"))
        response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.SOCIAL_AUTH_GOOGLE_CLIENT_ID,
                "client_secret": settings.SOCIAL_AUTH_GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        return response.json().get("access_token")

    def get_user(self, pk):
        """Returns a user instance"""
        try:
            return selectors.user_list(pk=pk).get()
        except User.DoesNotExist:
            return None

    def authenticate(self, request, code=None, **kwargs):
        """
        Authentication function for Custom google token verification
        parms:
            code - Google code received from view
        """
        if code:
            access_token = self._get_access_token(request, code)
            if access_token:
                google_user_details = requests.get(
                    f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
                )
                # FIXME:
                xxx = google_user_details.json()
                print(xxx)
                email = xxx.get("email")
                try:
                    user = selectors.user_list(email=email).get()
                    return user
                except User.DoesNotExist:
                    return None
