import pytest
from django.db import IntegrityError

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership, Project, Role


@pytest.mark.django_db
def test_user_email_unique():
    User.objects.create_user(email="a@example.com", password="x")
    with pytest.raises(IntegrityError):
        User.objects.create_user(email="a@example.com", password="y")


@pytest.mark.django_db
def test_user_password_hashed():
    user = User.objects.create_user(email="h@example.com", password="plain")
    assert user.password != "plain"
    assert user.check_password("plain")


@pytest.mark.django_db
def test_membership_unique_per_user_org():
    user = User.objects.create_user(email="m@example.com", password="x")
    org = Organization.objects.create(name="Acme", slug="acme")
    OrganizationMembership.objects.create(user=user, organization=org, role=Role.MEMBER)
    with pytest.raises(IntegrityError):
        OrganizationMembership.objects.create(user=user, organization=org, role=Role.VIEWER)


@pytest.mark.django_db
def test_project_slug_unique_per_organization():
    org_a = Organization.objects.create(name="A", slug="org-a")
    org_b = Organization.objects.create(name="B", slug="org-b")
    Project.objects.create(organization=org_a, name="Web", slug="web")
    Project.objects.create(organization=org_b, name="Web", slug="web")
    with pytest.raises(IntegrityError):
        Project.objects.create(organization=org_a, name="Other", slug="web")
