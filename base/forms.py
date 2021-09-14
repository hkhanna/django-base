from django import forms
from allauth.account import forms as auth_forms


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
