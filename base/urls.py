import django.views.defaults
from django.http import Http404
from django.urls import path, include
from . import views

page_not_found = lambda request: django.views.defaults.page_not_found(request, None)

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("terms/", views.TermsView.as_view(), name="terms_of_use"),
    path("privacy/", views.PrivacyPolicyView.as_view(), name="privacy_policy"),
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
    path("400/", lambda request: django.views.defaults.bad_request(request, None)),
    path(
        "403/", lambda request: django.views.defaults.permission_denied(request, None)
    ),
    path("404/", page_not_found),
    path("500/", django.views.defaults.server_error),
]
