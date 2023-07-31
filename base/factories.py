from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from faker import Faker
from allauth.account import models as auth_models
from .models import EmailMessage, Org, Plan
from . import services

fake = Faker()

User = get_user_model()


def user_create(**kwargs):
    first_name = fake.first_name()
    last_name = fake.last_name()

    defaults = dict(
        first_name=first_name,
        last_name=last_name,
        email=f"{first_name}.{last_name}@example.com".lower(),
        password="goodpass",
    )
    params = defaults | kwargs
    user = User.objects.create_user(**params)
    auth_models.EmailAddress.objects.get_or_create(
        user=user, email=user.email, primary=True
    )
    return user


def email_message_create(**kwargs):
    defaults = dict(created_by=user_create(), template_context=dict())
    params = defaults | kwargs

    return EmailMessage.objects.create(**params)


def org_create(**kwargs):
    defaults = dict(
        name=fake.company(),
        owner=user_create(),
        primary_plan=plan_create(),
        default_plan=plan_create(),
        current_period_end=timezone.now() + timedelta(days=10),
        is_personal=False,
    )
    params = defaults | kwargs

    return services.org_create(**params)


def plan_create():
    name = "Plan " + fake.word()
    return Plan.objects.create(name=name)
