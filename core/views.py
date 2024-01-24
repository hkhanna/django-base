import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import (
    update_session_auth_hash,
    get_user_model,
)
from django.contrib.auth.forms import (
    AuthenticationForm as DjangoLoginForm,
    PasswordChangeForm,
    SetPasswordForm,
    PasswordResetForm as DjangoPasswordResetForm,
)
from django.contrib.auth.views import (
    RedirectURLMixin,
    LoginView as DjangoLoginView,
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
)
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.http import Http404, JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import redirect, render as django_render
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import (
    TemplateView,
    View,
    FormView,
)
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.http import HttpResponseRedirect


from . import selectors, services, utils
from .exceptions import ApplicationError
from .tasks import email_message_webhook_process as email_message_webhook_process_task

User = get_user_model()

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

    return django_render(request, template, context)


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


@csrf_exempt
@require_http_methods(["POST"])
def email_message_webhook_view(request):
    try:
        webhook = services.email_message_webhook_create_from_request(
            body=request.body, headers=request.headers
        )
    except ApplicationError as e:
        return JsonResponse({"detail": str(e)}, status=400)

    logger.info(f"EmailMessageWebhook.id={webhook.id} received")
    email_message_webhook_process_task.delay(webhook.id)

    return JsonResponse({"detail": "Created"}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def event_emit_view(request):
    """Emit an Event via webhook."""
    try:
        payload = utils.validate_request_body_json(
            body=request.body, required_keys=["type"]
        )
    except ApplicationError as e:
        return JsonResponse({"detail": str(e)}, status=400)

    type = payload.pop("type")

    # Verify shared secret
    secret = request.META.get("HTTP_X_EVENT_SECRET")
    if secret != settings.EVENT_SECRET:
        return JsonResponse({"detail": "Invalid payload"}, status=400)

    services.event_emit(type=type, data=payload)

    return JsonResponse({"detail": "Created"}, status=201)


class HttpInertiaExternalRedirect(HttpResponseRedirect):
    status_code = 409

    def __init__(self, redirect_to: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(redirect_to, *args, **kwargs)
        self["X-Inertia-Location"] = self["Location"]


class LoginView(DjangoLoginView):
    redirect_authenticated_user = True

    class LoginForm(DjangoLoginForm):
        """Custom form for email address normalization, error messages and timezone-handling"""

        error_messages = {
            "invalid_login": "Please enter a correct %(username)s and password.",
            "inactive": "This account is inactive.",  # This is never used in the default authentication backend.
        }
        detected_tz = forms.CharField(max_length=254, required=False)

        def clean_username(self):
            """Normalize email to lowercase."""
            username = self.cleaned_data["username"].lower()
            return username

    def form_valid(self, form):
        services.user_login(
            request=self.request,
            user=form.get_user(),
            detected_tz=form.cleaned_data["detected_tz"],
        )
        return redirect(self.get_success_url())

    authentication_form = LoginForm

    def render_to_response(self, context, *args, **kwargs):
        return utils.inertia_render(
            self.request,
            "core/Login",
            props={
                "errors": context["form"].errors,
                "social_auth": {
                    "google": settings.SOCIAL_AUTH_GOOGLE_ENABLED,
                    "google_authorization_uri": services.GoogleOAuthService(
                        self.request, "login"
                    ).get_authorization_uri(),
                },
            },
            template_data={
                "html_class": "h-full bg-zinc-50",
                "body_class": "h-full dark:bg-zinc-900",
            },
        )


class GoogleLoginCallbackView(RedirectURLMixin, View):
    next_page = settings.LOGIN_REDIRECT_URL

    def get(self, request):
        error = request.GET.get("error")
        code = request.GET.get("code")
        detected_tz = request.GET.get("state", "")

        try:
            if error:
                raise ApplicationError(f"Could not log in with Google. Error: {error}")

            if code:
                oauth_service = services.GoogleOAuthService(request, "login")
                user, _ = oauth_service.attempt_login(
                    request=request, code=code, detected_tz=detected_tz
                )
                if user:
                    return redirect(self.get_success_url())
                else:
                    # No account on login fails. But existing account on signup just logs you in.
                    messages.error(
                        request,
                        "This account does not exist.",
                        extra_tags="Please sign up.",
                    )
                    return redirect("user:login")

        except ApplicationError as e:
            logger.exception(e)
            messages.error(request, str(e))
            return redirect("user:login")


class SignupView(RedirectURLMixin, FormView):
    next_page = settings.LOGIN_REDIRECT_URL
    redirect_authenticated_user = True

    class SignupForm(forms.Form):
        email = forms.EmailField(max_length=254, required=True)
        first_name = forms.CharField(max_length=150, required=True)
        last_name = forms.CharField(max_length=150, required=True)
        password = forms.CharField(max_length=254, required=True)
        detected_tz = forms.CharField(max_length=254, required=False)

        # Honeypot
        middle_initial = forms.CharField(max_length=150, required=False)

        def clean_email(self):
            """Normalize email to lowercase and verify uniqueness."""
            email = self.cleaned_data["email"]
            if selectors.user_list(email__iexact=email).exists():
                raise ValidationError("A user with that email already exists.")
            email = email.lower()
            return email

        def clean_password(self):
            password = self.cleaned_data["password"]
            validate_password(self.cleaned_data["password"])
            return password

        def clean(self):
            cleaned_data = super().clean()

            # Check honeypot
            honeypot = cleaned_data.pop("middle_initial", None)
            if honeypot:
                raise ValidationError("Signup closed.")
            return cleaned_data

    form_class = SignupForm

    @method_decorator(sensitive_post_parameters())
    def dispatch(self, request, *args, **kwargs):
        # Globally disable signup
        if services.global_setting_get_value("disable_signup"):
            return self.render_to_response(context={}, disable_signup=True)

        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        detected_tz = form.cleaned_data.pop("detected_tz")
        user = services.user_create(**form.cleaned_data)
        services.user_login(request=self.request, user=user, detected_tz=detected_tz)
        messages.success(self.request, f"Welcome {user.name}!")
        return super().form_valid(form)

    def render_to_response(self, context, *args, **kwargs):
        if kwargs.get("disable_signup"):
            return utils.inertia_render(
                self.request,
                "core/SignupDisabled",
                template_data={
                    "html_class": "h-full bg-zinc-50",
                    "body_class": "h-full dark:bg-zinc-900",
                },
            )

        return utils.inertia_render(
            self.request,
            "core/Signup",
            props={
                "errors": context["form"].errors,
                "social_auth": {
                    "google": settings.SOCIAL_AUTH_GOOGLE_ENABLED,
                    "google_authorization_uri": services.GoogleOAuthService(
                        self.request, "signup"
                    ).get_authorization_uri(),
                },
            },
            template_data={
                "html_class": "h-full bg-zinc-50",
                "body_class": "h-full dark:bg-zinc-900",
            },
        )


class GoogleSignupCallbackView(RedirectURLMixin, View):
    next_page = settings.LOGIN_REDIRECT_URL

    def get(self, request):
        error = request.GET.get("error")
        code = request.GET.get("code")
        detected_tz = request.GET.get("state", "")

        try:
            if error:
                raise ApplicationError(f"Could not sign up with Google. Error: {error}")

            if code:
                oauth_service = services.GoogleOAuthService(request, "signup")
                # First, try logging in in case the user already has an account.
                # Google also gives us the name of the user that we can use if we need to create an account.
                user, user_info = oauth_service.attempt_login(
                    request=request, code=code, detected_tz=detected_tz
                )
                if user:
                    return redirect(self.get_success_url())
                else:
                    user = oauth_service.signup_from_user_info(user_info)
                    services.user_login(
                        request=request,
                        user=user,
                        detected_tz=detected_tz,
                        event_type="user.login.google",
                    )
                    messages.success(self.request, f"Welcome {user.name}!")
                    return redirect(self.get_success_url())
        except ApplicationError as e:
            logger.exception(e)
            messages.error(request, str(e))
            return redirect("user:signup")


class ProfileView(LoginRequiredMixin, FormView):
    class ProfileForm(forms.Form):
        first_name = forms.CharField(max_length=150, required=True)
        last_name = forms.CharField(max_length=150, required=True)
        display_name = forms.CharField(max_length=300, required=False)
        email = forms.EmailField(required=True)

        def clean_email(self):
            """Normalize email to lowercase and verify uniqueness."""
            email = self.cleaned_data["email"]
            if (
                selectors.user_list(email__iexact=email)
                .exclude(pk=self.request.user.pk)
                .exists()
            ):
                raise ValidationError("A user with that email already exists.")
            email = email.lower()
            return email

    form_class = ProfileForm

    def get_initial(self):
        return {
            "first_name": self.request.user.first_name,
            "last_name": self.request.user.last_name,
            "display_name": self.request.user.display_name,
            "email": self.request.user.email,
        }

    def get_form(self, form_class=None):
        # We have to attach the request to the form so we
        # know who the user is for email uniqueness validation.
        form = super().get_form(form_class)
        form.request = self.request
        return form

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        services.user_update(instance=self.request.user, **form.cleaned_data)
        messages.success(self.request, "Profile updated.")
        services.event_emit(
            type="user.update.profile",
            data={
                "user": str(self.request.user.uuid),
                "user_email": self.request.user.email,
            },
        )
        return super().form_valid(form)

    def render_to_response(self, context, *args, **kwargs):
        return utils.inertia_render(
            self.request,
            "core/Profile",
            props={
                "initial": context["form"].initial,
                "errors": context["form"].errors,
            },
        )


class PasswordChangeView(LoginRequiredMixin, FormView):
    @method_decorator(sensitive_post_parameters())
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_form_class(self):
        if self.request.user.has_usable_password():
            return PasswordChangeForm
        else:
            return SetPasswordForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Password changed.")

        # Updating the password logs out all other sessions for the user
        # except the current one.
        update_session_auth_hash(self.request, form.user)

        services.event_emit(
            type="user.update.password",
            data={
                "user": str(self.request.user.uuid),
                "user_email": self.request.user.email,
            },
        )

        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path

    def render_to_response(self, context, *args, **kwargs):
        return utils.inertia_render(
            self.request,
            "core/PasswordChange",
            props={
                "errors": context["form"].errors,
                "has_password": self.request.user.has_usable_password(),
            },
        )


class PasswordResetView(FormView):
    class PasswordResetForm(DjangoPasswordResetForm):
        def save(self, request):
            """
            Generate a one-use only link for resetting password and send it to the
            user.
            """
            email = self.cleaned_data["email"]
            for user in self.get_users(email):
                reset_path = reverse(
                    "user:password-reset-confirm",
                    kwargs={
                        "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                        "token": default_token_generator.make_token(user),
                    },
                )
                email_message = services.email_message_create(
                    created_by=user,
                    to_name=user.name,
                    to_email=user.email,
                    subject="Password Reset Request",
                    sender_name=settings.SITE_CONFIG["account_from_name"],
                    sender_email=settings.SITE_CONFIG["account_from_email"],
                    reply_to_name=settings.SITE_CONFIG["account_reply_to_name"] or "",
                    reply_to_email=settings.SITE_CONFIG["account_reply_to_email"] or "",
                    template_prefix="core/email/password_reset",
                    template_context={
                        "user_name": user.name,
                        "user_email": user.email,
                        "password_reset_url": request.build_absolute_uri(reset_path),
                    },
                )
                services.email_message_queue(email_message=email_message)

        def get_users(self, email):
            """Any active user can reset their password"""
            return selectors.user_list(is_active=True, email=email)

    form_class = PasswordResetForm

    def form_valid(self, form):
        form.save(request=self.request)
        services.event_emit(
            type="user.password_reset_request",
            data={"email": form.cleaned_data["email"]},
        )

        return super().form_valid(form)

    def get_success_url(self):
        return self.request.path

    def render_to_response(self, context, *args, **kwargs):
        return utils.inertia_render(
            self.request,
            "core/PasswordReset",
            props={"errors": context["form"].errors},
            template_data={
                "html_class": "h-full bg-zinc-50",
                "body_class": "h-full dark:bg-zinc-900",
            },
        )


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    success_url = reverse_lazy("user:login")
    post_reset_login = True
    post_reset_login_backend = "django.contrib.auth.backends.ModelBackend"

    def form_valid(self, form):
        response = super().form_valid(form)
        services.event_emit(
            type="user.update.password_reset",
            data={
                "user": str(self.request.user.uuid),
                "user_email": self.request.user.email,
            },
        )
        return response

    def render_to_response(self, context, *args, **kwargs):
        errors = {}
        form = context.get("form")
        if form and hasattr(form, "errors"):
            errors = form.errors

        return utils.inertia_render(
            self.request,
            "core/PasswordResetConfirm",
            props={"errors": errors, "validlink": context["validlink"]},
            template_data={
                "html_class": "h-full bg-zinc-50",
                "body_class": "h-full dark:bg-zinc-900",
            },
        )


class TermsOfUseView(TemplateView):
    def render_to_response(self, context, *args, **kwargs):
        return utils.inertia_render(
            self.request,
            "core/TermsOfUse",
            props={},
        )


class PrivacyPolicyView(TemplateView):
    def render_to_response(self, context, *args, **kwargs):
        return utils.inertia_render(
            self.request,
            "core/PrivacyPolicy",
            props={},
        )
