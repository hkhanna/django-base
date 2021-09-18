from django.contrib import messages
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
            "pi_form": forms.PersonalInformationForm(),
            "password_form": auth_forms.ChangePasswordForm(user=request.user),
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        change_password_form = auth_forms.ChangePasswordForm(
            data=request.POST, user=request.user
        )
        if change_password_form.is_valid():
            change_password_form.save()
            context = {
                "pi_form": forms.PersonalInformationForm(),
                "password_form": auth_forms.ChangePasswordForm(user=request.user),
            }
            messages.success(request, "Password successfully changed!")
            update_session_auth_hash(request, request.user)  # Don't log the user out
        else:
            context = {
                "pi_form": forms.PersonalInformationForm(),
                "password_form": change_password_form,
            }
        return render(request, self.template_name, context)


class PasswordChangeView(auth_views.PasswordChangeView):
    success_url = reverse_lazy("account_settings")

    def form_invalid(self, form):
        return redirect("account_settings")
