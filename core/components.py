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
