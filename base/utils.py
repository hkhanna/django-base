import json
from django.http import HttpRequest


# This is used to test formset submissions and to create synthetic formset data.
# See https://stackoverflow.com/a/64354805
def formset_post_data(formset, update=[]):
    """Return a dictionary payload of a formset that can be posted.
    `update` merges provided keys. Keys that are left out as left as-is."""
    prefix_template = formset.empty_form.prefix  # default is 'form-__prefix__'

    # extract formset data
    management_form_data = formset.management_form.initial

    # form.fields is a dict of the form's fields, including
    # fields added by (model)formset.add_fields such as -DELETE and -id.
    form_data_list = []
    for form in formset:
        form_dict = {}
        for bound_field in form:
            name = bound_field.name
            value = bound_field.value() or ""
            form_dict[name] = str(value)
        form_data_list.append(form_dict)

    # initialize the post data dict
    post_data = {}

    # add properly prefixed management form fields
    for key, value in management_form_data.items():
        prefix = prefix_template.replace("__prefix__", "")
        post_data[prefix + key] = str(value)

    # If we added forms, update the management form.
    # N.B. We don't deal with deletion here.
    if update:
        added = len(update) - len(form_data_list)
        if added > 0:
            post_data[prefix + "TOTAL_FORMS"] = len(update)
            empty = {bound_field.name: "" for bound_field in formset.empty_form}
            form_data_list.extend([empty] * added)

    # add properly prefixed data form fields
    for index, form_data in enumerate(form_data_list):
        for key, value in form_data.items():
            prefix = prefix_template.replace("__prefix__", f"{index}-")
            try:
                post_data[prefix + key] = update[index][key]
            except (IndexError, KeyError):
                post_data[prefix + key] = str(value)

    return post_data


def form_post_data(form, update={}):
    return {field.name: field.value() for field in form} | update


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


def validate_request_body_json(request: HttpRequest, required_keys=list) -> dict | None:
    """Validate that the request body is JSON and return the parsed JSON."""
    try:
        body = json.loads(request.body)
    except json.decoder.JSONDecodeError as e:
        body = {}

    # Ensure all required keys
    for key in required_keys:
        try:
            body[key]
        except KeyError:
            return None

    return body
