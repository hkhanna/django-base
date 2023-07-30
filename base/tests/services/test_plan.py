from ...models import Plan
from ... import factories, services


def test_plan_default_unique(user):
    """Setting a plan as default unsets default from all other plans."""
    assert Plan.objects.count() == 1  # default plan created when User was created
    assert Plan.objects.first().is_default is True

    plan = factories.plan_create()

    services.plan_update(instance=plan, is_default=True)

    assert user.personal_org.primary_plan.is_default is False  # Default flipped off
    assert plan.is_default is True  # Default turned on
