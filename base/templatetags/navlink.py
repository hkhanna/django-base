from django import template
from django.urls import reverse

register = template.Library()

BASE_CLASS = "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
CURRENT_CLASS = "border-indigo-500 text-gray-900"
NONCURRENT_CLASS = (
    "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
)

MOBILE_BASE_CLASS = "block pl-3 pr-4 py-2 border-l-4 text-base font-medium"
MOBILE_CURRENT_CLASS = "bg-indigo-50 border-indigo-500 text-indigo-700"
MOBILE_NONCURRENT_CLASS = "border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800"


@register.inclusion_tag("base/navlink.html", takes_context=True)
def navlink(context, url_name, name, mobile=False):
    if mobile:
        base_class = MOBILE_BASE_CLASS
        current_class = MOBILE_CURRENT_CLASS
        noncurrent_class = MOBILE_NONCURRENT_CLASS
    else:
        base_class = BASE_CLASS
        current_class = CURRENT_CLASS
        noncurrent_class = NONCURRENT_CLASS

    link_class = base_class + " "
    if context["request"].path == reverse(url_name):
        link_class += current_class
    else:
        link_class += noncurrent_class
    return {"url": url_name, "name": name, "class": link_class}
