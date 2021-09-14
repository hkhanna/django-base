from django import template

register = template.Library()


@register.filter
def input_class(value, extra_classes=""):
    widget = value.field.widget
    if value.errors:
        widget.attrs["class"] = ("form-input-error " + extra_classes).strip()
    else:
        widget.attrs["class"] = ("form-input " + extra_classes).strip()
    return value


@register.filter
def checkbox_class(value, extra_classes=""):
    widget = value.field.widget
    if value.errors:
        widget.attrs["class"] = ("form-checkbox-error " + extra_classes).strip()
    else:
        widget.attrs["class"] = ("form-checkbox " + extra_classes).strip()
    return value
