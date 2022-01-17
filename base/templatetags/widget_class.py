from django import template

register = template.Library()


@register.filter
def widget_class(value, classes=""):
    # Conditional error classes would need to be done in the template.
    widget = value.field.widget
    widget.attrs["class"] = classes.strip()


@register.filter
def checkbox_class(value, extra_classes=""):
    # May eventually refactor this into a component if it becomes necessary.
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
