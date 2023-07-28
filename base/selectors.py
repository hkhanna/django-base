from typing import Union
from django.db.models import QuerySet, Model
from .models import Org, OrgInvitation, OrgUser


def org_list(**kwargs) -> QuerySet[Org]:
    return model_list(klass=Org, **kwargs)


def org_invitation_list(**kwargs) -> QuerySet[OrgInvitation]:
    return model_list(klass=OrgInvitation, **kwargs)


def org_user_list(**kwargs) -> QuerySet[OrgUser]:
    return model_list(klass=OrgUser, **kwargs)


def model_list(*, klass, **kwargs: Union[Model, str, bool]) -> QuerySet:
    return klass.objects.filter(**kwargs)
