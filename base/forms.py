import logging
from django import forms
from django.contrib.auth import get_user_model
from allauth.account import forms as auth_forms
from . import models
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email

logger = logging.getLogger(__name__)

User = get_user_model()


class LoginForm(auth_forms.LoginForm):
    def clean(self):
        """Inactive users should present as no user in the system, and locked users should be disallowed."""
        cleaned_data = super().clean()
        if not self.user.is_active:
            raise forms.ValidationError(self.error_messages["email_password_mismatch"])

        if self.user.is_locked:
            raise forms.ValidationError("This account has been locked.")

        return cleaned_data


class SignupForm(auth_forms.SignupForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "First name", "autocomplete": "given-name"}
        )
    )
    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Last name", "autocomplete": "family-name"}
        )
    )
    accept_terms = forms.BooleanField(required=True)

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
        required=True, widget=forms.TextInput(attrs={"autocomplete": "given-name"})
    )
    last_name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"autocomplete": "family-name"})
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
