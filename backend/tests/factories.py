import factory

from apps.accounts.models import User
from apps.ingestion.models import BuildEvent, BuildStatus, WebhookDelivery, WebhookProvider
from apps.organizations.models import Organization, OrganizationMembership, Project, Role


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password", "password123")
        return model_class.objects.create_user(password=password, *args, **kwargs)


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f"Organization {n}")
    slug = factory.Sequence(lambda n: f"org-{n}")


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f"Project {n}")
    slug = factory.Sequence(lambda n: f"project-{n}")


class OrganizationMembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationMembership

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = Role.MEMBER


class WebhookDeliveryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebhookDelivery

    project = factory.SubFactory(ProjectFactory)
    provider = WebhookProvider.GITHUB
    delivery_id = factory.Sequence(lambda n: f"delivery-{n}")


class BuildEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BuildEvent

    project = factory.SubFactory(ProjectFactory)
    status = BuildStatus.SUCCESS
    branch = "main"
    commit_sha = factory.Sequence(lambda n: f"{n:040x}"[:40])
    duration = 60
    raw_payload = factory.LazyFunction(dict)
