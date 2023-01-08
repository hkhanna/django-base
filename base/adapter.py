import waffle
import allauth.account.adapter
import allauth.socialaccount.adapter
from allauth.account.utils import user_email
from allauth.utils import email_address_exists
from allauth.account import app_settings as auth_settings
from allauth.socialaccount import app_settings as socialauth_settings
from django import forms
from django.conf import settings
from django.urls import reverse
from django.contrib import messages

from . import models


class AccountAdapter(allauth.account.adapter.DefaultAccountAdapter):
    def validate_unique_email(self, email):
        """Excludes 'inactive' user's email from blocking signup."""
        if models.User.objects.filter(email=email, is_active=True):
            raise forms.ValidationError(self.error_messages["email_taken"])
        return email

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse
        """
        return not waffle.switch_is_active("disable_signup")

    def respond_user_inactive(self, request, user):
        """We handle user active checking in the LoginForm.clean, so this function should never be reached."""
        raise NotImplementedError(
            "adapter respond_user_inactive should never be called"
        )

    def send_mail(self, template_prefix, email, context):
        """Replaces allauth email functions with our custom EmailMessage model"""

        # Need to remove from the context everything that can't be saved in a JSONField.
        user = context.pop("user")
        request = context.pop("request", None)
        current_site = context.pop("current_site", None)

        name = ""
        if user.first_name or user.last_name:
            name = user.name

        context["user_name"] = name or user.email
        context["user_email"] = user.email

        email_message = models.EmailMessage.objects.create(
            created_by=user,
            to_name=name,
            to_email=email,
            sender_name=settings.SITE_CONFIG["account_from_name"],
            sender_email=settings.SITE_CONFIG["account_from_email"],
            reply_to_name=settings.SITE_CONFIG["account_reply_to_name"] or "",
            reply_to_email=settings.SITE_CONFIG["account_reply_to_email"] or "",
            template_prefix=template_prefix,
            template_context=context,
        )
        email_message.send()


class SocialAccountAdapter(allauth.socialaccount.adapter.DefaultSocialAccountAdapter):
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account.
        """

        assert request.user.is_authenticated
        url = reverse("account_settings")
        return url

    def is_auto_signup_allowed(self, request, sociallogin):
        # If email is specified, check for duplicate and if so, no auto signup.
        auto_signup = socialauth_settings.AUTO_SIGNUP
        if auto_signup:
            email = user_email(sociallogin.user)
            # Let's check if auto_signup is really possible...
            if email:
                if auth_settings.UNIQUE_EMAIL:
                    if email_address_exists(email):
                        # Oops, another user already has this address.
                        # We cannot simply connect this social account
                        # to the existing user. Reason is that the
                        # email adress may not be verified, meaning,
                        # the user may be a hacker that has added your
                        # email address to their account in the hope
                        # that you fall in their trap.  We cannot
                        # check on 'email_address.verified' either,
                        # because 'email_address' is not guaranteed to
                        # be verified.
                        auto_signup = False
                        messages.error(
                            request,
                            self.error_messages["email_taken"]
                            % sociallogin.account.get_provider().name,
                        )
            elif socialauth_settings.EMAIL_REQUIRED:
                # Nope, email is required and we don't have it yet...
                auto_signup = False
        return auto_signup
