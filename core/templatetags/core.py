from django.conf import settings
from django import template

register = template.Library()


@register.simple_tag
def environment():
    return settings.ENVIRONMENT
