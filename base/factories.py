from datetime import timedelta
from django.utils import timezone
import factory
from factory.faker import faker
from allauth.account import models as auth_models

fake = faker.Faker()  # This is to use faker without the factory_boy wrapper


class PrimaryEmailAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth_models.EmailAddress
        django_get_or_create = (
            "user",
            "email",
        )

    user = None
    email = factory.LazyAttribute(lambda o: o.user.email)
    primary = True


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.User"
        django_get_or_create = ("email",)

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda obj: f"{obj.first_name}.{obj.last_name}@example.com".lower()
    )
    password = "goodpass"
    emailaddress_set = factory.RelatedFactory(
        PrimaryEmailAddressFactory, factory_related_name="user"
    )

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override the default ``_create`` with our custom call."""
        manager = cls._get_manager(model_class)

        # We have to manually implement the get_or_create functionality because we've overriden this function.
        existing = manager.filter(email=kwargs["email"]).first()
        if existing:
            return existing
        else:
            # The default would use ``manager.create(*args, **kwargs)``
            return manager.create_user(*args, **kwargs)


class EmailMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.EmailMessage"

    created_by = factory.SubFactory(UserFactory)
    template_context: dict = {}


class PlanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.Plan"

    name = factory.Faker("pystr")


class OrgFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.Org"

    name = factory.Faker("company")
    owner = factory.SubFactory(UserFactory)
    primary_plan = factory.SubFactory(PlanFactory)
    default_plan = factory.SubFactory(PlanFactory)
    current_period_end = factory.LazyFunction(
        lambda: timezone.now() + timedelta(days=10)
    )
    is_personal = False
