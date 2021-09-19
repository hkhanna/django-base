from django import template
from django.contrib.messages.constants import SUCCESS, INFO

register = template.Library()


@register.inclusion_tag("components/alert.html")
def alert(text, subtext=None, alertClass=None, variant=SUCCESS):
    colors = {
        SUCCESS: {
            "bg_color": "bg-green-100",
            "icon": "check-circle",
            "icon_color": "text-green-500",
            "text_color": "text-green-800",
            "subtext_color": "text-green-700",
            "button_color": "bg-green-100 text-green-700 hover:bg-green-100 focus:ring-green-600",
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
    return {"text": text, "subtext": subtext, "class": alertClass, **colors[variant]}


@register.inclusion_tag("components/button.html")
def button(
    type="button",
    name=None,
    value=None,
    variant="primary",
    size="md",
    left_icon=None,
    right_icon=None,
    disabled=False,
    extra_class="",
    text="Button",
    href=None,
):
    """Versatile Button component that can be used for different Button variants. Does tooltips, confirmable states, fetching states and more.

    Parameters
    ----------
    type : str
        The button type to be passed to the button element, e.g., "submit".
        If you pass the "href" parameter, this is ignored.
    name: str
        A "name" attribute passed to the button. Useful with type="submit".
    value: str
        A "value" attribute passed to the button. Useful with type="submit".
    variant : {"primary", "secondary", "white", "danger", "text-normal", "text-light"}
        The style of the button.
    size : {"xs", "sm", "md", "lg", "xl"}
        The size of the button.
    left_icon : str
        Heroicon to show to the left of the text.
    right_icon : str
        Heroicon to show to the right of the text.
    disabled : bool
        Is the button disabled?
    extra_class: str
        Additional classes to add to the button.
    text: str
        The text displayed in the button.
    href: str
        If this is passed, the button becomes an anchor element
    """
    is_text = variant.split("-")[0] == "text"
    icon_only = not bool(text)
    el = "button"
    if href:
        el = "a"

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
    left_icon_class = f"{icon_size_class} {left_icon_spacing_class}"
    right_icon_class = f"{icon_size_class} {right_icon_spacing_class}"

    button_class = f"{common} {variant_class} {size_class} {extra_class}"
    return {
        "el": el,
        "type": type,
        "name": name,
        "value": value,
        "button_class": button_class,
        "left_icon": left_icon,
        "right_icon": right_icon,
        "left_icon_class": left_icon_class,
        "right_icon_class": right_icon_class,
        "disabled": disabled,
        "text": text,
        "href": href,
    }
