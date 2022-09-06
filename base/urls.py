import django.views.defaults
from django.http import HttpResponse
from django.conf import settings
from django.views.generic import TemplateView, RedirectView
from django.urls import path, include
from . import views

page_not_found = lambda request: django.views.defaults.page_not_found(request, None)

urlpatterns = [
    path("", RedirectView.as_view(url=settings.LOGIN_URL), name="index"),
    path(
        "terms/",
        TemplateView.as_view(template_name="base/terms.html"),
        name="terms_of_use",
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="base/privacy.html"),
        name="privacy_policy",
    ),
    path("accounts/settings/", views.SettingsView.as_view(), name="account_settings"),
    path(
        "accounts/resend-confirmation-email/",
        views.ResendConfirmationEmailView.as_view(),
        name="account_resend_confirmation_email",
    ),
    path("accounts/delete/", views.DeleteView.as_view(), name="account_delete"),
    path("accounts/password/change/", page_not_found, name="account_change_password"),
    path(
        "accounts/password/set/",
        page_not_found,
        name="account_set_password",
    ),
    path("accounts/inactive/", page_not_found, name="account_inactive"),
    path("accounts/email/", page_not_found, name="account_email"),
    path(
        "accounts/confirm-email/",
        page_not_found,
        name="account_email_verification_sent",
    ),
    path("accounts/", include("allauth.urls")),
    path(
        "render-template-debug/<path:template>",
        views.render_template_with_params,
        name="render_template_debug",
    ),
    path("health_check/", lambda request: HttpResponse(""), name="health_check"),
    path("400/", lambda request: django.views.defaults.bad_request(request, None)),
    path("404/", page_not_found),
    path("500/", django.views.defaults.server_error),
    path(
        "robots.txt",
        views.TemplateView.as_view(
            template_name="base/robots.txt", content_type="text/plain"
        ),
    ),
]

# Only enable email message webhooks if a path has been provided.
if settings.EMAIL_MESSAGE_WEBHOOK_PATH:
    urlpatterns += [
        path(
            settings.EMAIL_MESSAGE_WEBHOOK_PATH,
            views.email_message_webhook_view,
            name="email_message_webhook",
        )
    ]
