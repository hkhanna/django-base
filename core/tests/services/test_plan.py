from .. import factories
from ...models import Plan
from ... import services


def test_plan_default_unique_create():
    """Setting a plan as default on create unsets default from all other plans."""
    plan1 = services.plan_create(name="Plan 1", is_default=True)
    assert Plan.objects.count() == 1
    assert Plan.objects.first().is_default is True

    plan2 = services.plan_create(name="Plan 2", is_default=True)

    plan1.refresh_from_db()
    assert plan1.is_default is False  # Default flipped off
    assert plan2.is_default is True  # Default turned on


def test_plan_default_unique_update():
    """Setting a plan as default on update unsets default from all other plans."""
    plan1 = services.plan_create(name="Plan 1", is_default=True)
    assert Plan.objects.count() == 1
    assert Plan.objects.first().is_default is True

    plan2 = factories.plan_create()

    services.plan_update(instance=plan2, is_default=True)

    plan1.refresh_from_db()
    assert plan1.is_default is False  # Default flipped off
    assert plan2.is_default is True  # Default turned on
