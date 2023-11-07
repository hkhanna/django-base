from django import template

register = template.Library()


# HACK: Remove this and refactor into a component.
@register.filter
def checkbox_class(value, extra_classes=""):
    widget = value.field.widget
    if value.errors:
        widget.attrs["class"] = (
            "rounded ring-2 ring-red-300 focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-red-300"
            + " "
            + extra_classes
        ).strip()
    else:
        widget.attrs["class"] = (
            "rounded focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300"
            + " "
            + extra_classes
        ).strip()
    return value
