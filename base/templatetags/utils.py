from django import template
from django.conf import settings

register = template.Library()


@register.filter
def keyvalue(dict, key):
    """Usage: {{dictionary|keyvalue:key_variable}}"""
    return dict[key]
