from django import forms
from django.forms.utils import ErrorDict


def serialize_form(form):
    """Serialize the relevant bits of a form"""
    return {"data": form.data, "errors": form.errors}


def serialize_formset(formset):
    """Serialize the relevant bits of a formset"""
    return {
        "data": formset.data,
        "errors": [f.errors for f in formset],
        "non_form_errors": formset.non_form_errors(),
    }


def rehydrate_form(form_class, serialized, *args, **kwargs):
    """Rehydrate a form from a serialized representation"""
    form = form_class(serialized["data"], *args, **kwargs)
    form._errors = ErrorDict()
    form.cleaned_data = {}
    for field, error in serialized["errors"].items():
        form.add_error(field, error)
    return form


def rehydrate_formset(formset_class, serialized, *args, **kwargs):
    """Rehydrate a formset from a serialized representation"""
    formset = formset_class(serialized["data"], *args, **kwargs)

    # Rehydrating a formset's errors are a little bit tricky.
    # We try to emulate the way Django does it by adding the
    # error to each individual form and then also collecting them
    # into FormSet._errors.
    formset._errors = []
    for i, f in enumerate(formset):
        f._errors = ErrorDict()
        f.cleaned_data = {}
        for field, error in serialized["errors"][i].items():
            f.add_error(field, error)
        formset._errors.append(f.errors)

    # We also need to rehydrate any "non_form_errors" since that's not
    # handled elsewhere.
    formset._non_form_errors = formset.error_class(serialized["non_form_errors"])
    return formset


def form_to_prg(request, form):
    """Given a request and a form, save a serialized version of the form to the session."""
    session_key = "prg_context__" + form.__class__.__name__
    if isinstance(form, forms.BaseForm):
        request.session[session_key] = serialize_form(form)
    elif isinstance(form, forms.BaseFormSet):
        request.session[session_key] = serialize_formset(form)
    else:
        raise RuntimeError("Only a Form or FormSet may be passed to form_to_prg.")


def form_from_prg(request, form_class, *args, **kwargs):
    """Given a request and form_class, instantiate the form based on any
    serialized representations in the session. If there are none, return a fresh
    instance of the form."""
    session_key = "prg_context__" + form_class.__name__
    serialized = request.session.pop(session_key, None)
    if serialized:
        if issubclass(form_class, forms.BaseForm):
            return rehydrate_form(form_class, serialized, *args, **kwargs)
        elif issubclass(form_class, forms.BaseFormSet):
            return rehydrate_formset(form_class, serialized, *args, **kwargs)
        else:
            raise RuntimeError("Only a Form or FormSet may be passed to form_from_prg.")
    else:
        return form_class(*args, **kwargs)


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
