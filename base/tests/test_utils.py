from django import forms
from django.contrib.auth import get_user_model
from ..utils import (
    serialize_form,
    serialize_formset,
    formset_post_data,
    rehydrate_form,
    rehydrate_formset,
)
from ..factories import fake

User = get_user_model()


class UserForm(forms.ModelForm):
    class Meta:
        fields = ["first_name", "last_name"]
        model = User

    def clean(self):
        raise forms.ValidationError("Error in clean")

    def clean_first_name(self):
        raise forms.ValidationError("Error in clean_first_name")


def test_form():
    """Confirm that the expected data and errors are on the form fixture."""
    data = {"first_name": fake.first_name(), "last_name": fake.last_name()}
    form = UserForm(data)
    form.is_valid()

    assert form.data == data
    assert form.errors == {
        "__all__": ["Error in clean"],
        "first_name": ["Error in clean_first_name"],
    }


def test_serialize_form():
    """Given a form, serialize the data and errors to a dict."""
    data = {"first_name": fake.first_name(), "last_name": fake.last_name()}
    form = UserForm(data)
    form.is_valid()

    serialized = serialize_form(form)
    assert serialized["data"] == data
    assert serialized["errors"] == {
        "__all__": ["Error in clean"],
        "first_name": ["Error in clean_first_name"],
    }


def test_rehydrate_form():
    """Given a serialized form, rehydrate into the appropriate instance."""
    serialized = {
        "data": {"first_name": fake.first_name(), "last_name": fake.last_name()},
        "errors": {
            "__all__": ["Error in clean"],
            "first_name": ["Error in clean_first_name"],
        },
    }

    form = rehydrate_form(UserForm, serialized)
    assert form.data == serialized["data"]
    assert form.is_bound is True
    assert form.errors == serialized["errors"]


def test_serialize_formset(user):
    """Given a formset, serialize the data and errors to a dict."""
    UserFormSet = forms.modelformset_factory(User, UserForm, extra=0)
    formset = UserFormSet(
        queryset=User.objects.all()
    )  # One user in the system from the user fixture
    data = formset_post_data(formset)

    formset = UserFormSet(data, queryset=User.objects.all())
    formset.is_valid()

    serialized = serialize_formset(formset)
    assert serialized["data"] == data
    assert serialized["errors"] == [
        {
            "__all__": ["Error in clean"],
            "first_name": ["Error in clean_first_name"],
        }
    ]
    assert serialized["non_form_errors"] == []


def test_rehydrate_formset(user):
    """Given a serialized formset, rehydrate into the appropriate instance."""
    UserFormSet = forms.modelformset_factory(User, UserForm, extra=0)
    formset = UserFormSet(
        queryset=User.objects.all()
    )  # One user in the system from the user fixture
    data = formset_post_data(formset)

    serialized = {
        "data": data,
        "errors": [
            {
                "__all__": ["Error in clean"],
                "first_name": ["Error in clean_first_name"],
            }
        ],
        "non_form_errors": [],
    }
    formset = rehydrate_formset(UserFormSet, serialized)
    assert formset.data == serialized["data"]
    assert formset.is_bound is True
    assert formset.errors == serialized["errors"]
