import waffle
import allauth.account.adapter

from . import models


class AccountAdapter(allauth.account.adapter.DefaultAccountAdapter):
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
            template_prefix=template_prefix,
            template_context=context,
        )
        email_message.send()
