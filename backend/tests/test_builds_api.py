import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.ingestion.models import BuildStatus
from apps.organizations.models import OrganizationMembership, Project, Role
from tests.factories import BuildEventFactory, OrganizationFactory, UserFactory


def build_list_url(org_id, project_id):
    return reverse("build-list", kwargs={"org_id": org_id, "project_id": project_id})


@pytest.fixture
def auth_client():
    def _auth(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _auth


@pytest.fixture
def org_with_roles():
    org = OrganizationFactory(slug="acme-corp", name="Acme")
    admin = UserFactory(email="admin@example.com")
    member = UserFactory(email="member@example.com")
    viewer = UserFactory(email="viewer@example.com")
    outsider = UserFactory(email="outsider@example.com")
    OrganizationMembership.objects.create(user=admin, organization=org, role=Role.ADMIN)
    OrganizationMembership.objects.create(user=member, organization=org, role=Role.MEMBER)
    OrganizationMembership.objects.create(user=viewer, organization=org, role=Role.VIEWER)
    project = Project.objects.create(organization=org, name="API", slug="api")
    return {
        "org": org,
        "admin": admin,
        "member": member,
        "viewer": viewer,
        "outsider": outsider,
        "project": project,
    }


@pytest.mark.django_db
class TestBuildListAPI:
    def test_list_requires_auth(self, org_with_roles):
        data = org_with_roles
        response = APIClient().get(build_list_url(data["org"].id, data["project"].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_viewer_can_list_builds(self, auth_client, org_with_roles):
        data = org_with_roles
        BuildEventFactory(project=data["project"], branch="main", status=BuildStatus.SUCCESS)
        response = auth_client(data["viewer"]).get(build_list_url(data["org"].id, data["project"].id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["branch"] == "main"
        assert "raw_payload" not in response.data[0]

    def test_non_member_forbidden(self, auth_client, org_with_roles):
        data = org_with_roles
        response = auth_client(data["outsider"]).get(
            build_list_url(data["org"].id, data["project"].id)
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_wrong_org_returns_404(self, auth_client, org_with_roles):
        data = org_with_roles
        other_org = OrganizationFactory(slug="other-org")
        OrganizationMembership.objects.create(
            user=data["admin"],
            organization=other_org,
            role=Role.ADMIN,
        )
        url = build_list_url(other_org.id, data["project"].id)
        assert auth_client(data["admin"]).get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_ordering_and_limit(self, auth_client, org_with_roles):
        data = org_with_roles
        for i in range(55):
            BuildEventFactory(
                project=data["project"],
                branch=f"branch-{i:02d}",
                commit_sha=f"{i:040x}"[:40],
            )
        response = auth_client(data["viewer"]).get(build_list_url(data["org"].id, data["project"].id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 50
        branches = [row["branch"] for row in response.data]
        assert branches == sorted(branches, key=lambda b: int(b.split("-")[1]), reverse=True)
