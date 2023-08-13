from django.core.exceptions import ImproperlyConfigured
from django_components import component


@component.register("input_field")
class InputField(component.Component):
    def get_template_name(self, context={}):
        style = context.get("style", "normal")
        if style == "normal":
            return "components/form/input_normal.html"
        elif style == "with_overlapping_label":
            return "components/form/input_with_overlapping_label.html"
        else:
            raise ImproperlyConfigured(
                f"Unrecognized style attribute '{style}' in Component {self.__class__.__name__}"
            )

    def get_widget_class(self, style, is_error, extra_class):
        # default_class should only include borders, rings, shadows, and text size.
        default_classes = {
            "normal": "rounded-md shadow-sm border border-gray-300 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none sm:text-sm",
            "normal_error": "rounded-md shadow-sm border ring-2 ring-red-300 border-red-300 focus:ring-indigo-500 focus:border-indigo-500 focus:outline-none sm:text-sm",
            # For the with_overlapping_label style, the input always has to be w-full or it will
            # not work properly.
            # Note that the error state goes on the outside div, not the input, which is why
            # the two are identical here.
            "with_overlapping_label": "w-full border-0 p-0 focus:ring-0 sm:text-sm",
            "with_overlapping_label_error": "w-full border-0 p-0 focus:ring-0 sm:text-sm",
        }

        if not is_error:
            widget_class = default_classes[style]
        else:
            widget_class = default_classes[style + "_error"]

        return (widget_class + " " + extra_class).strip()

    def get_context_data(self, field, style="normal", input_class=""):
        widget = field.field.widget
        widget.attrs["class"] = self.get_widget_class(
            style=style, is_error=bool(field.errors), extra_class=input_class
        )

        return {"field": field, "style": style}
