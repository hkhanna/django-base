import json
from django.contrib.messages.constants import (
    DEFAULT_LEVELS,
    SUCCESS,
    WARNING,
    INFO,
    ERROR,
)
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django_components import component


@component.register("page_heading")
class PageHeading(component.Component):
    template_name = "components/page_heading.html"

    def get_context_data(self, heading):
        has_actions = "actions" in self.slots
        return {"heading": heading, "has_actions": has_actions}


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
            ERROR: {
                "bg_color": "bg-red-50",
                "icon": "x-circle",
                "icon_color": "text-red-400",
                "text_color": "text-red-800",
                "subtext_color": "text-red-700",
                "button_color": "bg-red-50 text-red-800 hover:bg-red-50 focus:ring-red-700",
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


@component.register("modal")
class Modal(component.Component):
    template_name = "components/modal.html"

    def get_context_data(self, aria_label, show="modal"):
        return {"aria_label": aria_label, "show": show}


@component.register("submit_modal")
class SubmitModal(component.Component):
    template_name = "components/submit_modal.html"

    def get_context_data(
        self,
        title,
        variant,
        submit_button_text,
        show="modal",
        text=None,
        icon=None,
        name=None,
        value=None,
        formnovalidate=None,
    ):
        variant_settings = {
            "primary": {
                "icon": icon or "check-circle",
                "icon_bg_color": "bg-indigo-100",
                "icon_color": "text-indigo-700",
            },
            "secondary": {
                "icon": icon or "information",
                "icon_bg_color": "bg-blue-100",
                "icon_color": "text-blue-500",
            },
            "danger": {
                "icon": icon or "exclamation",
                "icon_bg_color": "bg-red-100",
                "icon_color": "text-red-600",
            },
        }
        return {
            "title": title,
            "aria_label": title,
            "text": text,
            "variant": variant,
            "submit_button_text": submit_button_text,
            "show": show,
            "name": name,
            "value": value,
            "formnovalidate": formnovalidate,
            **variant_settings[variant],
        }


@component.register("button")
class Button(component.Component):
    template_name = "components/button.html"

    def get_context_data(
        self,
        type="button",
        variant="primary",
        size="md",
        left_icon=None,
        right_icon=None,
        left_icon_style_class="",
        right_icon_style_class="",
        disabled=False,
        extra_class="",
        text="Button",
        href=None,
        click=None,
        formnovalidate=None,
        x="{}",
        **kwargs,
    ):
        """Versatile Button component that can be used for different Button variants.

        Parameters
        ----------
        type : str
            The button type to be passed to the button element, e.g., "submit".
            If you pass the "href" parameter, this is ignored.
        variant : {"primary", "secondary", "white", "danger", "text-normal", "text-light"}
            The style of the button.
        size : {"xs", "sm", "md", "lg", "xl"}
            The size of the button.
        left_icon : str
            Heroicon to show to the left of the text.
        right_icon : str
            Heroicon to show to the right of the text.
        left_icon_style_class : str
            Classes to apply to the left icon. Should only be styling and not spacing or size.
        right_icon_style_class : str
            Classes to apply to the right icon. Should only be styling and not spacing or size.
        disabled : bool
            Is the button disabled?
        extra_class: str
            Additional classes to add to the button.
        text: str
            The text displayed in the button.
        href: str
            If this is passed, the button becomes an anchor element. Can pass url name or real url.
        formnovalidate: bool
            If this is passed, put the `formnovalidate` attribute on the button element.
        click: str
            If this is passed, the value becomes the x-on:click attribute on the button.
        x: str of JSON that will parse to a dict
            For use with AlpineJS. The keys of the dict will map to the values of the dict.
            For example x="{'bind:disabled': 'isDisabled'}" will render x-bind:disabled="isDisabled"
            on the button element. 'click', above, is a special case of this and is handled
            separately for backwards compatibility reasons.
        **kwargs:
            Any other kwargs are rendered directly on the button element, turning any underscores into dashes.
        """
        is_text = variant.split("-")[0] == "text"
        icon_only = not bool(text)
        el = "button"
        if href:
            el = "a"
            try:
                href = reverse(href)
            except NoReverseMatch:
                pass

        normalized_kwargs = {}
        for key, value in kwargs.items():
            new_key = key.replace("_", "-")
            normalized_kwargs[new_key] = value

        common = "inline-flex relative items-center font-medium focus:outline-none"

        variants = {
            "primary": {
                "common": "text-white border border-transparent shadow-sm rounded-md",
                "enabled": "bg-indigo-600 hover:bg-indigo-500 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500",
                "disabled": "cursor-default bg-indigo-300",
            },
            "secondary": {
                "common": "border border-transparent shadow-sm rounded-md",
                "enabled": "text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500",
                "disabled": "cursor-default text-indigo-300 bg-indigo-100",
            },
            "white": {
                "common": "border bg-white shadow-sm rounded-md",
                "enabled": "border-gray-300 text-gray-700 hover:bg-gray-50 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500",
                "disabled": "cursor-default border-gray-200 text-gray-400",
            },
            "danger": {
                "common": "border border-transparent text-white shadow-sm rounded-md",
                "enabled": "bg-red-600 hover:bg-red-500 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500",
                "disabled": "cursor-default bg-red-400",
            },
            "text-normal": {
                "common": "",
                "enabled": "text-indigo-700 hover:text-indigo-500 focus:text-indigo-500",
                "disabled": "cursor-default text-indigo-300",
            },
            "text-light": {
                "common": "",
                "enabled": "text-indigo-500 hover:text-indigo-300 focus:text-indigo-300",
                "disabled": "cursor-default text-indigo-300",
            },
            "text-gray": {
                "common": "",
                "enabled": "text-gray-500 hover:text-gray-700 hover:border-gray-300 ",
                "disabled": "cursor-default",
            },
            "text-danger": {
                "common": "",
                "enabled": "text-red-700 hover:text-red-500 focus:text-red-500",
                "disabled": "cursor-default text-red-300",
            },
        }
        variant_class = variants[variant]["common"]
        if not disabled:
            variant_class += " " + variants[variant]["enabled"]
        else:
            variant_class += " " + variants[variant]["disabled"]

        sizes = {
            "xs": {
                # There is no need for a text: key since it would just be blank. If that changes, feel free to add text-specific size classes.
                "common": "text-xs leading-4",
                "btn": "px-2.5 py-1.5",
            },
            "sm": {
                "common": "text-sm leading-4",
                "btn": "px-3 py-2",
            },
            "md": {
                "common": "text-sm leading-5",
                "btn": "px-4 py-2",
            },
            "lg": {
                "common": "text-base leading-6",
                "btn": "px-4 py-2",
            },
            "xl": {
                "common": "text-base leading-6",
                "btn": "px-5 py-3",
            },
        }
        size_class = sizes[size]["common"]
        if not is_text:
            size_class += " " + sizes[size]["btn"]

        icon_sizes = {
            "xs": "h-4 w-4",
            "sm": "h-4 w-4",
            "md": "h-5 w-5",
            "lg": "h-6 w-6",
            "xl": "h-6 w-6",
        }
        icon_size_class = icon_sizes[size]

        icon_spacing = {
            "xs": {
                "left": {
                    "btn": "-ml-0.5 mr-2",  # Non text-* variants that have children in the button (i.e., not icon-only)
                    "textWithChildren": "mr-1",  # Text-* variants that have children in the button (i.e., not icon-only)
                },
                "right": {
                    "btn": "-mr-0.5 ml-2",
                    "text": "ml-1",
                },
            },
            "sm": {
                "left": {
                    "btn": "-ml-1 mr-2",
                    "text": "mr-1",
                },
                "right": {
                    "btn": "-mr-1 ml-2",
                    "text": "ml-1",
                },
            },
            "md": {
                "left": {
                    "btn": "-ml-1 mr-2",
                    "text": "mr-1",
                },
                "right": {
                    "btn": "-mr-1 ml-2",
                    "text": "ml-1",
                },
            },
            "lg": {
                "left": {
                    "btn": "-ml-1 mr-3",
                    "text": "mr-3",
                },
                "right": {
                    "btn": "-mr-1 ml-3",
                    "text": "ml-3",
                },
            },
            "xl": {
                "left": {
                    "btn": "-ml-1 mr-3",
                    "text": "mr-3",
                },
                "right": {
                    "btn": "-mr-1 ml-3",
                    "text": "ml-3",
                },
            },
        }
        if icon_only:
            left_icon_spacing_class = ""
            right_icon_spacing_class = ""
        elif is_text:
            left_icon_spacing_class = icon_spacing[size]["left"]["text"]
            right_icon_spacing_class = icon_spacing[size]["right"]["text"]
        else:
            left_icon_spacing_class = icon_spacing[size]["left"]["btn"]
            right_icon_spacing_class = icon_spacing[size]["right"]["btn"]
        left_icon_class = (
            f"{icon_size_class} {left_icon_spacing_class} {left_icon_style_class}"
        )
        right_icon_class = (
            f"{icon_size_class} {right_icon_spacing_class} {right_icon_style_class}"
        )

        button_class = f"{common} {variant_class} {size_class} {extra_class}"
        return {
            "el": el,
            "type": type,
            "button_class": button_class,
            "left_icon": left_icon,
            "right_icon": right_icon,
            "left_icon_class": left_icon_class,
            "right_icon_class": right_icon_class,
            "disabled": disabled,
            "text": text,
            "href": href,
            "formnovalidate": formnovalidate,
            "click": click,
            "x": json.loads(x),
            "kwargs": normalized_kwargs,
        }


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
