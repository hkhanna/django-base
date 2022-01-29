from django import template
from django.conf import settings

register = template.Library()


@register.inclusion_tag("base/gtag.html")
def gtag():
    return {"ga_tracking_id": settings.GA_TRACKING_ID}
