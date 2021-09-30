from django_components import component
from django.contrib.messages.constants import DEFAULT_LEVELS, SUCCESS, WARNING, INFO


@component.register("alert")
class Alert(component.Component):
    template_name = "components/alert.html"

    def get_context_data(
        self, text, variant=SUCCESS, dismissable=True, alertClass=None
    ):

        # So you can pass in "info" or "success" as a variant.
        if isinstance(variant, str):
            variant = DEFAULT_LEVELS[variant.upper()]

        colors = {
            SUCCESS: {
                "bg_color": "bg-green-100",
                "icon": "check-circle",
                "icon_color": "text-green-500",
                "text_color": "text-green-800",
                "subtext_color": "text-green-700",
                "button_color": "bg-green-100 text-green-700 hover:bg-green-100 focus:ring-green-600",
            },
            WARNING: {
                "bg_color": "bg-yellow-50",
                "icon": "exclamation",
                "icon_color": "text-yellow-400",
                "text_color": "text-yellow-800",
                "subtext_color": "text-yellow-600",
                "button_color": "bg-yellow-50 text-yellow-700 hover:bg-yellow-50 focus:ring-yellow-600",
            },
            INFO: {
                "bg_color": "bg-blue-100",
                "icon": "information-circle",
                "icon_color": "text-blue-500",
                "text_color": "text-blue-700",
                "subtext_color": "text-blue-600",
                "button_color": "bg-blue-100 text-blue-700 hover:bg-blue-100 focus:ring-blue-600",
            },
        }

        has_subtext = "subtext" in self.slots
        return {
            "text": text,
            "dismissable": dismissable,
            "class": alertClass,
            "has_subtext": has_subtext,
            **colors[variant],
        }
