import django.views.defaults
from allauth.account import views as auth_views
from django.conf import settings
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView, TemplateView
from django.contrib.auth.views import LogoutView

from . import views

page_not_found = lambda request: django.views.defaults.page_not_found(request, None)

user_patterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

urlpatterns = [
    path("user/", include((user_patterns, "user"))),
    path("", RedirectView.as_view(url=settings.LOGIN_URL), name="index"),
    path(
        "terms/",
        TemplateView.as_view(template_name="core/terms.html"),
        name="terms_of_use",
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="core/privacy.html"),
        name="privacy_policy",
    ),
    path("org/switch/", views.OrgSwitchView.as_view(), name="org_switch"),
    path("org/invitation/", views.OrgInvitationCreateView.as_view(), name="org_invite"),
    path(
        "org/invitation/<uuid:uuid>/cancel/",
        views.OrgInvitationCancelView.as_view(),
        name="org_invitation_cancel",
    ),
    path(
        "org/invitation/<uuid:uuid>/resend/",
        views.OrgInvitationResendView.as_view(),
        name="org_invitation_resend",
    ),
    path("org/", views.OrgDetailView.as_view(), name="org_detail"),
    path("event/emit/", views.event_emit_view, name="event_emit"),
    path(
        "accounts/settings/", views.UserSettingsView.as_view(), name="account_settings"
    ),
    path(
        "accounts/resend-confirmation-email/",
        views.ResendConfirmationEmailView.as_view(),
        name="account_resend_confirmation_email",
    ),
    path("accounts/delete/", views.AccountDeleteView.as_view(), name="account_delete"),
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
    # This intercepts the page when a social signup fails because the email belongs to someone else.
    # For whatever reason, reverse resolves the name backwards...
    path("accounts/login/", auth_views.signup, name="socialaccount_signup"),
    path(
        "render-template-debug/<path:template>",
        views.render_template_with_params,
        name="render_template_debug",
    ),
    path("health_check/", lambda request: HttpResponse(""), name="health_check"),
    path(
        settings.EMAIL_MESSAGE_WEBHOOK_PATH,
        views.email_message_webhook_view,
        name="email_message_webhook",
    ),
    path(
        "400/", lambda request: django.views.defaults.bad_request(request, Exception())
    ),
    path("404/", page_not_found),
    path("500/", django.views.defaults.server_error),
    path(
        "robots.txt",
        views.TemplateView.as_view(
            template_name="core/robots.txt", content_type="text/plain"
        ),
    ),
]
