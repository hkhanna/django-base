import waffle
import logging
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.conf import settings
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import TemplateView, View, DetailView, CreateView, DeleteView
from django.contrib.auth import update_session_auth_hash, get_user_model
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
from .models import (
    User as UserType,
)  # mypy: Can't use get_user_model because of https://github.com/typeddjango/django-stubs/issues/599

from . import forms, models, services, selectors, utils, tasks
from .permissions import OUSettingPermissionMixin
from .exceptions import ApplicationError, ApplicationWarning

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


class OrgSwitchView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            services.org_switch(request=request, slug=request.POST.get("slug"))
        except ObjectDoesNotExist as e:
            logger.exception(e)
            raise Http404()
        return redirect("index")


class OrgDetailView(LoginRequiredMixin, DetailView):
    template_name = "base/org_detail.html"

    def get_object(self, *args, **kwargs):
        return self.request.org


class OrgInvitationCreateView(LoginRequiredMixin, OUSettingPermissionMixin, CreateView):
    model = models.OrgInvitation
    fields = ("email",)
    ou_setting = "can_invite_members"
    permission_denied_message = "You don't have permission to invite a user."

    def form_valid(self, form):
        try:
            org_invitation = services.org_invitation_validate_new(
                org=self.request.org,
                created_by=self.request.user,
                org_invitation=form.instance,
            )
            services.org_invitation_send(org_invitation=org_invitation)
        except ApplicationError as e:
            messages.error(self.request, str(e))
        except ApplicationWarning as e:
            messages.warning(self.request, str(e))
        else:
            messages.success(
                self.request,
                f"{form.instance.email} has been invited to {self.request.org.name}.",
            )
        return redirect("org_detail")

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email address in invitation.")
        return redirect("org_detail")


class OrgInvitationCancelView(
    LoginRequiredMixin, OUSettingPermissionMixin, SuccessMessageMixin, DeleteView
):
    object: UserType  # mypy: Workaround to a mypy bug. See https://github.com/typeddjango/django-stubs/issues/1227
    slug_field = "uuid"
    slug_url_kwarg = "uuid"
    ou_setting = "can_invite_members"
    permission_denied_message = "You don't have permission to cancel an invitation."
    success_url = reverse_lazy("org_detail")
    success_message = "Invitation canceled."

    def get_queryset(self):
        return selectors.org_invitation_list(org=self.request.org)


class OrgInvitationResendView(
    LoginRequiredMixin,
    OUSettingPermissionMixin,
    View,
):
    ou_setting = "can_invite_members"
    permission_denied_message = "You don't have permission to resend an invitation."

    def post(self, request, uuid):
        try:
            services.org_invitation_resend(org=request.org, uuid=uuid)
        except ObjectDoesNotExist as e:
            logger.exception(e)
            raise Http404()

        messages.success(request, "Invitation resent.")
        return redirect("org_detail")


class UserSettingsView(LoginRequiredMixin, View):
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


class AccountDeleteView(LoginRequiredMixin, auth_views.LogoutFunctionalityMixin, View):
    def post(self, request, *args, **kwargs):
        if waffle.switch_is_active("disable_account_deletion"):
            raise Http404("Account deletion is disabled.")

        with transaction.atomic():
            request.user.is_active = False
            request.user.save()
            request.user.emailaddress_set.update(verified=False)
            request.user.socialaccount_set.all().delete()
        messages.info(request, "Your account has been deleted.")
        self.logout()
        return redirect("account_login")


@csrf_exempt
@require_http_methods(["POST"])
def email_message_webhook_view(request):
    try:
        # FIXME: can use ApplicationError here now.
        webhook = services.email_message_webhook_create(request=request)
    except TypeError:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    logger.info(f"EmailMessageWebhook.id={webhook.id} received")
    tasks.process_email_message_webhook.delay(webhook.id)

    return JsonResponse({"detail": "Created"}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def event_emit_view(request):
    # FIXME: can use ApplicationError here now.
    payload = utils.validate_request_body_json(request, required_keys=["type"])
    if payload is None:
        return JsonResponse({"detail": "Invalid payload"}, status=400)
    type = payload.pop("type")

    # Verify shared secret
    secret = request.META.get("HTTP_X_EVENT_SECRET")
    if secret != settings.EVENT_SECRET:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    services.event_emit(type=type, data=payload)

    return JsonResponse({"detail": "Created"}, status=201)
