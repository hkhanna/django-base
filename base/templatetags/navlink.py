from django import template
from django.urls import reverse

register = template.Library()


default_classes = {
    "common": "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium",
    "current": "border-indigo-500 text-gray-900",
    "noncurrent": "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
    "mobile_common": "block pl-3 pr-4 py-2 border-l-4 text-base font-medium",
    "mobile_current": "bg-indigo-50 border-indigo-500 text-indigo-700",
    "mobile_noncurrent": "border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800",
}


@register.inclusion_tag("base/navlink.html", takes_context=True)
def navlink(context, url_name, name, mobile=False):
    classes = context.get("navlink_classes", default_classes)
    if mobile:
        base_class = classes["mobile_common"]
        current_class = classes["mobile_current"]
        noncurrent_class = classes["mobile_noncurrent"]
    else:
        base_class = classes["common"]
        current_class = classes["current"]
        noncurrent_class = classes["noncurrent"]

    link_class = base_class + " "
    if context["request"].path == reverse(url_name):
        link_class += current_class
    else:
        link_class += noncurrent_class
    return {"url": url_name, "name": name, "class": link_class}
