import waffle
import logging
import json
from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import TemplateView, View
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from allauth.account import (
    views as auth_views,
    forms as auth_forms,
    models as auth_models,
)
from allauth.account.adapter import get_adapter

from . import forms, models

logger = logging.getLogger(__name__)


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


def permission_denied(request, exception):
    """When a PermissionDenied exception is raised, redirect with a message."""
    try:
        message = str(exception.args[0])
    except IndexError:
        message = "Permission denied."
    messages.warning(request, message)

    try:
        url = exception.args[1]
    except IndexError:
        url = settings.PERMISSION_DENIED_REDIRECT

    return redirect(url)


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
        if request.user.has_usable_password():
            password_formclass = auth_forms.ChangePasswordForm
        else:
            password_formclass = auth_forms.SetPasswordForm

        context.update(
            {
                "pi_form": forms.PersonalInformationForm(instance=request.user),
                "password_form": password_formclass(user=request.user),
                "disconnect_form": forms.DisconnectForm(request=request),
                "disable_account_deletion": waffle.switch_is_active(
                    "disable_account_deletion"
                ),
            }
        )
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.POST.get("form_name") == "pi":
            pi_form = forms.PersonalInformationForm(
                data=request.POST, instance=request.user
            )
        else:
            pi_form = forms.PersonalInformationForm(instance=request.user)

        if request.user.has_usable_password():
            password_formclass = auth_forms.ChangePasswordForm
        else:
            password_formclass = auth_forms.SetPasswordForm

        if request.POST.get("form_name") == "password":
            password_form = password_formclass(data=request.POST, user=request.user)
        else:
            password_form = password_formclass(user=request.user)

        if request.POST.get("form_name") == "disconnect":
            disconnect_form = forms.DisconnectForm(data=request.POST, request=request)
        else:
            disconnect_form = forms.DisconnectForm(request=request)

        context = self.get_context_data()
        context.update(
            {
                "pi_form": pi_form,
                "password_form": password_form,
                "disconnect_form": disconnect_form,
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
            return redirect("account_settings")

        if password_form.is_valid():
            password_form.save()
            messages.success(request, "Password successfully changed.")
            update_session_auth_hash(request, request.user)  # Don't log the user out
            return redirect("account_settings")
        else:
            print(password_form.errors)

        if disconnect_form.is_valid():
            disconnect_form.save()
            messages.info(request, "The social account has been disconnected.")
            return redirect("account_settings")

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
        if waffle.switch_is_active("disable_account_deletion"):
            raise Http404("Account deletion is disabled.")

        with transaction.atomic():
            request.user.is_active = False
            request.user.save()
            request.user.emailaddress_set.update(verified=False)
        messages.info(request, "Your account has been deleted.")
        self.logout()
        return redirect("account_login")


@csrf_exempt
@require_http_methods(["POST"])
def email_message_webhook_view(request):
    try:
        payload = json.loads(request.body)
    except json.decoder.JSONDecodeError as e:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    if type(payload) != dict:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    headers = {}
    for key in request.headers:
        value = request.headers[key]
        if isinstance(value, str):
            headers[key] = value

    webhook = models.EmailMessageWebhook.objects.create(
        body=payload,
        headers=headers,
        status=models.EmailMessageWebhook.Status.NEW,
    )
    logger.info(f"EmailMessageWebhook.id={webhook.id} received")

    webhook.process()

    return JsonResponse({"detail": "Created"}, status=201)
