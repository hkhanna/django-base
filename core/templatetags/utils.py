from django import template

register = template.Library()


@register.filter
def keyvalue(dict, key):
    """Usage: {{dictionary|keyvalue:key_variable}}"""
    return dict[key]


@register.filter
def split(value, arg):
    """Usage: {{value|split:","}}"""
    return value.split(arg)
