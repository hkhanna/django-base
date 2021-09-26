import factory
from factory.faker import faker
from allauth.account import models as auth_models

fake = faker.Faker()  # This is to use faker without the factory_boy wrapper


class PrimaryEmailAddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auth_models.EmailAddress

    user = None
    email = factory.LazyAttribute(lambda o: o.user.email)
    primary = True


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.User"

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
        # The default would use ``manager.create(*args, **kwargs)``
        return manager.create_user(*args, **kwargs)


class EmailMessageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "base.EmailMessage"

    created_by = factory.SubFactory(UserFactory)
    template_context = {}
