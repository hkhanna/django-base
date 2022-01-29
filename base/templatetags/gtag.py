import waffle
from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("base/gtag.html", takes_context=True)
def gtag(context):
    # If there's a problem with any of this, don't bother.
    # This can happen, e.g., in a 404 situation where some info
    # is missing on the request.
    try:
        request = context["request"]

        if waffle.flag_is_active(request, "no_ga"):
            return None

    except Exception:
        return None

    return {"ga_tracking_id": settings.GA_TRACKING_ID}
