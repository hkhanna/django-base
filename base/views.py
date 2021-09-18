from django.contrib import messages
from django.contrib import auth
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.urls.base import reverse_lazy
from django.views.generic import TemplateView, View
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from allauth.account import views as auth_views, forms as auth_forms

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


class SettingsView(LoginRequiredMixin, View):
    template_name = "account/settings.html"

    def get(self, request, *args, **kwargs):
        context = {
            "pi_form": forms.PersonalInformationForm(instance=request.user),
            "password_form": auth_forms.ChangePasswordForm(user=request.user),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
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

        context = {"pi_form": pi_form, "password_form": password_form}

        if pi_form.is_valid():
            pi_form.save()
            messages.success(request, "Personal information saved.")

        if password_form.is_valid():
            password_form.save()
            messages.success(request, "Password successfully changed.")
            update_session_auth_hash(request, request.user)  # Don't log the user out

        return render(request, self.template_name, context)


class PasswordChangeView(auth_views.PasswordChangeView):
    success_url = reverse_lazy("account_settings")

    def form_invalid(self, form):
        return redirect("account_settings")
