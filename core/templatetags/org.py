from django import template
from django.urls import reverse

register = template.Library()


@register.inclusion_tag("base/_org_switcher.html", takes_context=True)
def org_switcher(context):
    request = context["request"]
    org_name_extended = request.org.name
    if request.org.is_personal:
        org_name_extended += " (Personal)"

    available_orgs = [
        {"name": org.name, "slug": org.slug}
        for org in request.user.orgs.filter(is_active=True)
        if org != request.org
    ]

    return {
        "org_name": request.org.name,
        "org_name_extended": org_name_extended,
        "user_email": request.user.email,
        "available_orgs": available_orgs,
    }
