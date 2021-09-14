import django.views.defaults
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
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
    path("404/", lambda request: django.views.defaults.page_not_found(request, None)),
    path("500/", django.views.defaults.server_error),
]
