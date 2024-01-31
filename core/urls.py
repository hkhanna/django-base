from django.conf import settings
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView
from django.contrib.auth.views import LogoutView

from . import views


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
    path(
        "google/login/callback/",
        views.GoogleLoginCallbackView.as_view(),
        name="google-login-callback",
    ),
    path(
        "google/signup/callback/",
        views.GoogleSignupCallbackView.as_view(),
        name="google-signup-callback",
    ),
]

urlpatterns = [
    path("user/", include((user_patterns, "user"))),
    path(
        "no-organization-found/", views.OrgRequiredView.as_view(), name="org-required"
    ),
    path("", RedirectView.as_view(url=settings.LOGIN_URL), name="index"),
    path(
        "terms/",
        views.TermsOfUseView.as_view(),
        name="terms_of_use",
    ),
    path(
        "privacy/",
        views.PrivacyPolicyView.as_view(),
        name="privacy_policy",
    ),
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
        "robots.txt",
        views.TemplateView.as_view(
            template_name="core/robots.txt", content_type="text/plain"
        ),
    ),
    path("error/<int:status_code>/", views.ErrorTestView.as_view()),
]
