import uuid

import pytest
from rest_framework.test import APIRequestFactory

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership, Role
from apps.organizations.permissions import HasOrganizationRole, IsOrganizationMember, get_user_role


class DummyOrgView:
    def __init__(self, kwargs):
        self.kwargs = kwargs

    required_org_role = Role.MEMBER


@pytest.mark.django_db
def test_get_user_role():
    user = User.objects.create_user(email="rbac@example.com", password="x")
    org = Organization.objects.create(name="O", slug="slug-o")
    OrganizationMembership.objects.create(user=user, organization=org, role=Role.ADMIN)
    role = get_user_role(user, org.id)
    assert role == Role.ADMIN


@pytest.mark.django_db
def test_is_organization_member_permission():
    user = User.objects.create_user(email="mem@example.com", password="x")
    org = Organization.objects.create(name="O", slug="slug-m")
    OrganizationMembership.objects.create(user=user, organization=org, role=Role.VIEWER)
    factory = APIRequestFactory()
    request = factory.get("/dummy/")
    request.user = user

    permitted = IsOrganizationMember().has_permission(
        request,
        DummyOrgView({"org_id": str(org.id)}),
    )
    assert permitted is True

    denied = IsOrganizationMember().has_permission(
        request,
        DummyOrgView({"org_id": str(uuid.uuid4())}),
    )
    assert denied is False


@pytest.mark.django_db
def test_has_organization_role_permission():
    user = User.objects.create_user(email="role@example.com", password="x")
    org = Organization.objects.create(name="O", slug="slug-r")
    OrganizationMembership.objects.create(user=user, organization=org, role=Role.VIEWER)
    factory = APIRequestFactory()
    request = factory.get("/dummy/")
    request.user = user

    view_member = DummyOrgView({"org_id": str(org.id)})
    denied = HasOrganizationRole().has_permission(request, view_member)
    assert denied is False

    OrganizationMembership.objects.filter(user=user, organization=org).update(role=Role.MEMBER)
    allowed = HasOrganizationRole().has_permission(request, view_member)
    assert allowed is True
