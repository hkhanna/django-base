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
        <label for="{{ field.id_for_label }}" class="block text-sm font-medium text-zinc-700">{{ field.label }}</label>
        <div class="mt-1">
            {{field}}
        </div>
        {% if field.errors %}
            <p class="mt-2 text-sm text-red-600">{{field.errors|join:" "}}</p>
        {% endif %}
        </div>
        """,
        name="input",
    ).render(context)


@component.register("modal")
class Modal(component.Component):
    """Usage: {% modal show=<show> %}This is the modal body.{% endmodal %}"""

    template_name = "core/components/modal.html"


@component.register("modal-submit")
class ModalSubmit(component.Component):
    """Usage:
    {% modal-submit ...kwargs %}This is the body of the submit modal.{% endmodal-submit %}

    kwargs:
        show: The name of the variable that controls whether the modal is shown.
        title: The title of the modal.
        variant?: One of "primary", "secondary", "danger". Defaults to "primary"
        formnovalidate?: True or False. Defaults to False.
        icon?: The name of a heroicon. Default depends on the variant.
        label?: The label of the submit button.
        name?: The name of the submit button.
        value?: The value of the submit button.
        <attr>?: Any attribute that can be on a button of type=submit, such as formnovalidate or a non-ancestor form.
    """

    template_name = "core/components/modal_submit.html"

    def get_context_data(self, **kwargs) -> dict:
        variant = self.attributes.pop("variant", "primary")
        title = self.attributes.pop("title", "Untitled")
        label = self.attributes.pop("label", "Submit")
        variants = {
            "primary": {
                "default_icon": "check-circle",
                "icon_bg_color": "bg-indigo-100",
                "icon_color": "text-indigo-700",
            },
            "secondary": {
                "default_icon": "information",
                "icon_bg_color": "bg-blue-100",
                "icon_color": "text-blue-500",
            },
            "danger": {
                "default_icon": "exclamation-circle",
                "icon_bg_color": "bg-red-100",
                "icon_color": "text-red-600",
            },
        }
        icon = self.attributes.pop("icon", variants[variant]["default_icon"])
        icon_color = variants[variant]["icon_color"]
        icon_bg_color = variants[variant]["icon_bg_color"]

        return {
            "show": self.attributes.pop("show"),
            "variant": variant,
            "title": title,
            "label": label,
            "icon": icon,
            "icon_color": icon_color,
            "icon_bg_color": icon_bg_color,
        }


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
