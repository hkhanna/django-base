import json
from importlib import import_module
from typing import Callable, Optional, TYPE_CHECKING

from django.contrib.messages import get_messages

from inertia import render
from . import constants
from .exceptions import *

if TYPE_CHECKING:
    from .types import DjangoModelType


def inertia_render(request, component, props={}, template_data={}):
    """Inertia render function should include flash messages."""
    # I don't think you can do it in middleware because it can skip a message that was
    # added in the current request.
    storage = get_messages(request)
    messages = []
    for message in storage:
        # If the `extra_tags` parameter to `messages.add_message` is passed, the `extra_tags`
        # parameter becomes the title, and the text of the message is the description.

        if message.extra_tags:
            messages.append(
                {
                    "title": message.extra_tags,
                    "description": str(message),
                    "level": message.level_tag,
                }
            )
        else:
            messages.append({"title": str(message), "level": message.level_tag})

    return render(
        request,
        component,
        props={"messages": messages} | props,
        template_data=template_data,
    )


def get_email_display_name(
    user,
    header,
    email=None,
    suffix=None,
    max_length=78,
):
    """Generate a From: or Reply-To: display name that fits within max_length
    By default, max_length=78 conforms to https://www.rfc-editor.org/rfc/rfc5322#section-2.1.1
    """
    remaining = max_length
    remaining -= len(header)
    remaining -= 2  # Colon and space after header

    if suffix:
        remaining -= len(suffix)
        remaining -= 1  # The space before the suffix

    if not email:
        email = user.email

    remaining -= len(email)
    remaining -= 3  # Space before the email and the angle brackets.

    name = None
    if len(user.name) <= remaining:
        # Ideally we go, e.g., FullName via Magistrate <docs@getmagistrate.com>
        name = user.name

    if name is None and user.first_name and user.last_name:
        # If that exceeds 78 characters, we go, e.g., FirstInitial LastName via Magistrate <docs@getmagistrate.com>
        proposed = user.first_name[0] + ". " + user.last_name
        if len(proposed) <= remaining:
            name = proposed

    if name is None:
        # If that still exceeds 78 characters, use the user's initials via Magistrate.
        proposed = ""
        if user.first_name:
            proposed += user.first_name[0]
        if user.last_name:
            proposed += user.last_name[0]
        if proposed:
            name = proposed

    if name is None:
        # If the user doesn't have any name and their email address is so long we get here,
        # just truncate the email from the part before the @.
        name = user.email.split("@")[0]
        name = name[:remaining]

    if suffix:
        return f"{name} {suffix}"
    else:
        return name


def validate_request_body_json(
    *, body: str, required_keys: list | None = None
) -> list | dict:
    """Validate that the request body is JSON and return the parsed JSON."""
    try:
        body_json = json.loads(body)
    except json.decoder.JSONDecodeError as e:
        raise ApplicationError("Invalid payload")

    # Ensure all required keys
    if required_keys is None:
        required_keys = []

    for key in required_keys:
        try:
            body_json[key]
        except KeyError:
            raise ApplicationError("Invalid payload")

    return body_json


def trim_string(field: str) -> str:
    """Remove superfluous linebreaks and whitespace"""
    lines = field.splitlines()
    sanitized_lines = []
    for line in lines:
        sanitized_line = line.strip()
        if sanitized_line:  # Remove blank lines
            sanitized_lines.append(line.strip())
    sanitized = " ".join(sanitized_lines).strip()
    return sanitized


def get_snake_case(model: "DjangoModelType") -> str:
    verbose_name = model._meta.verbose_name
    if not verbose_name:
        raise ValueError(f"Model {model} has no verbose_name")
    return verbose_name.replace(" ", "_").lower()


def get_function_from_path(path: str) -> Callable:
    """Get a function from a string path"""
    module_name, function_name = path.rsplit(".", 1)
    module = import_module(module_name)
    return getattr(module, function_name)


def get_value_from_subtyped_keys(d: dict, key: str) -> Optional[str]:
    """Given a dict, return the value of the first key
    that matches the subtype or its ancestors."""
    # Used primarily for event handlers.
    while key:
        if key in d:
            return d[key]
        elif "." in key:
            key = ".".join(key.split(".")[:-1])
        else:
            break
    return None


def issubtype(subtype: str, type: str, inclusive=True) -> bool:
    """Return whether a key is a subtype of another key."""

    # Inclusive allows for an exact match
    if subtype == type:
        if inclusive:
            return True
        else:
            return False

    return subtype.startswith(type + ".")


def cast_setting(value: str, type: str) -> bool | int | str:
    """Cast a setting's value to its type"""
    if type == constants.SettingType.BOOL:
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            raise ValueError(f"Invalid boolean value: {value}")
    elif type == constants.SettingType.INT:
        return int(value)
    elif type == "str":
        return value
    else:
        raise ValueError(f"Invalid type: {type}")
