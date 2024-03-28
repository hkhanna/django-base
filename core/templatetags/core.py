from django.conf import settings
from django import template

register = template.Library()


@register.simple_tag
def admin_environment_color():
    if settings.ENVIRONMENT == "production":
        return "#15803d"
    else:
        return "#417690"
