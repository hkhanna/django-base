from django.shortcuts import render
from django.conf import settings
from django.http import Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import TemplateView

from . import forms


@staff_member_required
def render_template_with_params(request, template):
    """A view only accessible in DEBUG mode to render templates.
    Primarily used to render email templates in the browser."""
    if not settings.DEBUG:
        raise Http404("Path does not exist")
    context = {}
    for param in request.GET:
        context[param] = request.GET.get(param)

    return render(request, template, context)


class IndexView(TemplateView):
    template_name = "404.html"


class SettingsView(TemplateView):
    template_name = "account/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pi_form"] = forms.PersonalInformationForm()
        context["password_form"] = forms.ChangePasswordForm()
        return context
