from django import forms
from django.contrib.auth import get_user_model
from allauth.account import forms as auth_forms
from . import models

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
        widget=forms.TextInput(attrs={"placeholder": "First name"})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Last name"})
    )
    accept_terms = forms.BooleanField(required=True)


class PersonalInformationForm(forms.ModelForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    oldpassword = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"placeholder": "Current password"}),
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def clean_oldpassword(self):
        if not self.instance.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError("Please type your current password.")
        return self.cleaned_data["oldpassword"]
