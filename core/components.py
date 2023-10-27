from django_web_components import component
from django_web_components.template import CachedTemplate


@component.register
def input(context):
    field = context["attributes"].pop("field")

    widget_class = " ".join(["input", context["attributes"].pop("class", "")])
    if bool(field.errors):
        widget_class += " input-error"
    widget = field.field.widget
    widget.attrs["class"] = widget_class

    context["field"] = field

    return CachedTemplate(
        """
        <div>
        <label for="{{ field.id_for_label }}" class="block text-sm font-medium text-gray-700">{{ field.label }}</label>
        <div class="mt-1">
            {{field}}
        </div>
        {% if field.errors %}
            <p class="mt-2 text-sm text-red-600">{{field.errors|join:" "}}</p>
        {% endif %}
        </div>
        """
    ).render(context)


@component.register("modal")
class Modal(component.Component):
    template_name = "core/components/modal.html"


@component.register("alert")
class Alert(component.Component):
    """Usage:
    {% #alert level="info" dismissable=True headline="This is a headline" %}
    OR
    {% alert level="info" dismissable=True headline="This is a headline" %}This is an optional body.{% endalert %}
    """

    template_name = "core/components/alert.html"

    def get_context_data(self, **kwargs) -> dict:
        variant = self.attributes.pop("variant", "info")
        icons = {
            "success": "check-circle",
            "warning": "exclamation-circle",
            "info": "information-circle",
            "error": "x-circle",
        }
        colors = {
            "success": {
                "bg": "bg-green-100",
                "icon": "text-green-500",
                "headline": "text-green-800",
                "body": "text-green-700",
                "button": "bg-green-100 text-green-700 hover:bg-green-100 focus:ring-green-600",
            },
            "warning": {
                "bg": "bg-yellow-50",
                "icon": "text-yellow-400",
                "headline": "text-yellow-800",
                "body": "text-yellow-600",
                "button": "bg-yellow-50 text-yellow-700 hover:bg-yellow-50 focus:ring-yellow-600",
            },
            "info": {
                "bg": "bg-blue-100",
                "icon": "text-blue-500",
                "headline": "text-blue-700",
                "body": "text-blue-600",
                "button": "bg-blue-100 text-blue-700 hover:bg-blue-100 focus:ring-blue-600",
            },
            "error": {
                "bg": "bg-red-50",
                "icon": "text-red-400",
                "headline": "text-red-800",
                "body": "text-red-700",
                "button": "bg-red-50 text-red-800 hover:bg-red-50 focus:ring-red-700",
            },
        }

        return {
            "colors": colors[variant],
            "icon": icons[variant],
        }
