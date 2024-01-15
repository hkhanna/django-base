import django.views.defaults
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
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("settings/profile/", views.ProfileView.as_view(), name="profile"),
    path(
        "settings/password/", views.PasswordChangeView.as_view(), name="password-change"
    ),
    path("password-reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "password-reset/<str:uidb64>/<str:token>/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
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
