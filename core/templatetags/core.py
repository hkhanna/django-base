from django import template
from heroicons.templatetags import heroicons

from core.exceptions import *

register = template.Library()


@register.filter
def keyvalue(dict, key):
    """Usage: {{dictionary|keyvalue:key_variable}}"""
    return dict[key]


@register.filter
def split(value, arg):
    """Usage: {{value|split:","}}"""
    return value.split(arg)


@register.simple_tag
def heroicon(name, variant="outline", **kwargs):
    if variant == "outline":
        return heroicons.heroicon_outline(name, **kwargs)
    elif variant == "solid":
        return heroicons.heroicon_solid(name, **kwargs)
    elif variant == "mini":
        return heroicons.heroicon_mini(name, **kwargs)
    else:
        raise ApplicationError(f"Invalid variant: {variant}")
