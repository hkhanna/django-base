from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.urls.base import reverse_lazy
from django.views.generic import TemplateView, View
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from allauth.account import (
    views as auth_views,
    forms as auth_forms,
    models as auth_models,
)
from allauth.account.adapter import get_adapter

from . import forms


@staff_member_required
def render_template_with_params(request, template):
    """A view only accessible in DEBUG mode to render templates.
    Primarily used to render email templates in the browser."""
    if not settings.DEBUG:
        raise Http404("Path does not exist")
    context = {}
    for param in request.GET:
        context[param] = request.GET.get(param)

    return render(request, template, context)


class IndexView(TemplateView):
    template_name = "404.html"


class TermsView(TemplateView):
    template_name = "base/terms.html"


class PrivacyPolicyView(TemplateView):
    template_name = "base/privacy.html"


class SettingsView(LoginRequiredMixin, View):
    template_name = "account/settings.html"

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
        except AttributeError:
            context = {"billing_enabled": False}
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context.update(
            {
                "pi_form": forms.PersonalInformationForm(instance=request.user),
                "password_form": auth_forms.ChangePasswordForm(user=request.user),
            }
        )
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user_email = request.user.email
        if request.POST.get("form_name") == "pi":
            pi_form = forms.PersonalInformationForm(
                data=request.POST, instance=request.user
            )
        else:
            pi_form = forms.PersonalInformationForm(instance=request.user)

        if request.POST.get("form_name") == "password":
            password_form = auth_forms.ChangePasswordForm(
                data=request.POST, user=request.user
            )
        else:
            password_form = auth_forms.ChangePasswordForm(user=request.user)

        context = self.get_context_data()
        context.update(
            {
                "pi_form": pi_form,
                "password_form": password_form,
            }
        )

        if pi_form.is_valid():
            pi_form.save()
            email_address = request.user.sync_changed_email()
            if email_address:
                email_address.send_confirmation()
                messages.success(
                    request,
                    "Personal information saved. A confirmation email has been sent to your new email address.",
                )
            else:
                messages.success(request, "Personal information saved.")

        if password_form.is_valid():
            password_form.save()
            messages.success(request, "Password successfully changed.")
            update_session_auth_hash(request, request.user)  # Don't log the user out

        return render(request, self.template_name, context)


class ResendConfirmationEmailView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        email_address = auth_models.EmailAddress.objects.filter(
            user=request.user, verified=False
        ).first()
        if email_address:
            get_adapter(request).add_message(
                request,
                messages.INFO,
                "account/messages/" "email_confirmation_sent.txt",
                {"email": email_address.email},
            )
            email_address.send_confirmation(request)
        return redirect("account_settings")


class DeleteView(LoginRequiredMixin, auth_views.LogoutFunctionalityMixin, View):
    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            request.user.is_active = False
            request.user.save()
            request.user.emailaddress_set.update(verified=False)
        messages.info(request, "Your account has been deleted.")
        self.logout()
        return redirect("account_login")
