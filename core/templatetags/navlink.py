import re
from django import template
from django.urls import reverse

register = template.Library()


default_classes = {
    "common": "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium",
    "current": "border-indigo-500 text-zinc-900",
    "noncurrent": "border-transparent text-zinc-500 hover:text-zinc-700 hover:border-zinc-300",
    "mobile_common": "block pl-3 pr-4 py-2 border-l-4 text-base font-medium",
    "mobile_current": "bg-indigo-50 border-indigo-500 text-indigo-700",
    "mobile_noncurrent": "border-transparent text-zinc-600 hover:bg-zinc-50 hover:border-zinc-300 hover:text-zinc-800",
}


@register.inclusion_tag("core/includes/navlink.html", takes_context=True)
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
    # If the url_name is in the parent part of the path of the current request
    # we say it's the current class.
    if re.match(reverse(url_name), context["request"].path):
        link_class += current_class
    else:
        link_class += noncurrent_class
    return {"url": url_name, "name": name, "class": link_class}
