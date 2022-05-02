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
