import logging

import pytz
from allauth.account import forms as auth_forms
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.socialaccount import forms as socialauth_forms
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from . import models

logger = logging.getLogger(__name__)

User = get_user_model()


class LoginForm(auth_forms.LoginForm):
    remember = forms.BooleanField(
        label="Remember Me",
        required=False,
        widget=forms.CheckboxInput(attrs={"checked": True}),
    )
    detected_tz = forms.CharField(
        max_length=254, required=False, widget=forms.HiddenInput
    )

    def clean(self):
        """Inactive users should present as no user in the system, and locked users should be disallowed."""
        cleaned_data = super().clean()
        if not cleaned_data:
            return
        if not self.user.is_active:
            raise forms.ValidationError(self.error_messages["email_password_mismatch"])

        if self.user.is_locked:
            raise forms.ValidationError("This account has been locked.")

        return cleaned_data

    def login(self, request, redirect_url=None):
        ret = super().login(request, redirect_url)

        # Set the user's timezone in their session if it was provided
        detected_tz = self.cleaned_data["detected_tz"]
        if detected_tz:
            try:
                tz = pytz.timezone(detected_tz)
                request.session["detected_tz"] = detected_tz
                timezone.activate(tz)
            except pytz.exceptions.UnknownTimeZoneError:
                logger.warning(
                    f"User.email={self.cleaned_data['login']} Bad timezone {detected_tz}"
                )

        return ret


class SignupForm(auth_forms.SignupForm):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"placeholder": "First name", "autocomplete": "given-name"}
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={"placeholder": "Last name", "autocomplete": "family-name"}
        ),
    )

    # Honeypot
    middle_initial = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Middle initial"}),
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()

        # Check honeypot
        honeypot = cleaned_data.get("middle_initial")
        if honeypot:
            raise ValidationError("Signup sadly closed.")
        return cleaned_data

    def clean_email(self):
        self.cleaned_data["email"] = self.cleaned_data["email"].lower()
        return super().clean_email()

    def save(self, request):
        adapter = get_adapter(request)
        # Reactivate soft deleted users if they exist
        user = models.User.objects.filter(
            email=self.cleaned_data["email"], is_active=False
        ).first()
        if user:
            user.is_active = True
            adapter.save_user(request, user, self)
        else:
            user = adapter.new_user(request)
            adapter.save_user(request, user, self)
            setup_user_email(request, user, [])
        return user


class PersonalInformationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    email = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"autocomplete": "email"})
    )
    oldpassword = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(
            attrs={"placeholder": "Current password", "id": "pi_oldpassword"}
        ),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.has_usable_password():
            del self.fields["oldpassword"]

    def clean_oldpassword(self):
        if not self.instance.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError("Please type your current password.")
        return self.cleaned_data["oldpassword"]

    def clean_email(self):
        """Normalize email to lowercase and handle the edge case of a collision with a deleted user."""
        email = self.cleaned_data["email"].lower()

        # If there's a deleted user with this email, change the deleted user's email to something
        # unique.
        deleted_user = models.User.objects.filter(is_active=False, email=email).first()
        if deleted_user:
            logger.warning(f"User changing email to deleted user's email {email}")
            name, domain = deleted_user.email.rsplit("@", 1)
            name = name + "+" + str(deleted_user.pk)
            deleted_user.email = "@".join([name, domain])
            deleted_user.save()
            deleted_user.sync_changed_email()

        return email


class DisconnectForm(socialauth_forms.DisconnectForm):
    def clean(self):
        try:
            super().clean()
        except ValidationError as e:
            for message in e.messages:
                messages.error(self.request, message)
            raise
