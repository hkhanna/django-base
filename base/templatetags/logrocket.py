from django import template
from django.conf import settings
from django.urls import resolve

register = template.Library()


@register.inclusion_tag("base/logrocket.html", takes_context=True)
def logrocket(context):
    request = context["request"]

    current_view = resolve(request.path_info).view_name
    if current_view in settings.LOGROCKET_EXCLUDED_VIEWS:
        return None

    user = request.user
    if user.is_authenticated:
        return {
            "logrocket_id": settings.LOGROCKET_APP_ID,
            "user_id": user.pk,
            "user_name": user.name,
            "user_email": user.email,
        }
    else:
        return {"logrocket_id": settings.LOGROCKET_APP_ID}
