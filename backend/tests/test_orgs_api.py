import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.organizations.models import Organization, OrganizationMembership, Project, Role
from tests.factories import OrganizationFactory, UserFactory


def org_detail_url(org_id):
    return reverse("organization-detail", kwargs={"org_id": org_id})


def project_list_url(org_id):
    return reverse("project-list", kwargs={"org_id": org_id})


def project_detail_url(org_id, project_id):
    return reverse("project-detail", kwargs={"org_id": org_id, "project_id": project_id})


def membership_list_url(org_id):
    return reverse("membership-list", kwargs={"org_id": org_id})


def membership_detail_url(org_id, membership_id):
    return reverse(
        "membership-detail",
        kwargs={"org_id": org_id, "membership_id": membership_id},
    )


@pytest.fixture
def auth_client():
    def _auth(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _auth


@pytest.fixture
def org_with_roles():
    """Org with admin, member, viewer, and outsider users."""

    def _build():
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

    return _build


@pytest.mark.django_db
class TestOrganizationAPI:
    def test_list_requires_auth(self):
        response = APIClient().get(reverse("organization-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_only_user_orgs(self, auth_client):
        user = UserFactory()
        mine = OrganizationFactory(slug="mine")
        OrganizationFactory(slug="other")
        OrganizationMembership.objects.create(user=user, organization=mine, role=Role.MEMBER)
        response = auth_client(user).get(reverse("organization-list"))
        assert response.status_code == status.HTTP_200_OK
        slugs = {row["slug"] for row in response.data}
        assert slugs == {"mine"}

    def test_create_org_grants_admin_membership(self, auth_client):
        user = UserFactory()
        response = auth_client(user).post(
            reverse("organization-list"),
            {"name": "New Co", "slug": "new-co"},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        org = Organization.objects.get(slug="new-co")
        membership = OrganizationMembership.objects.get(user=user, organization=org)
        assert membership.role == Role.ADMIN

    def test_create_rejects_duplicate_slug(self, auth_client):
        OrganizationFactory(slug="taken")
        user = UserFactory()
        response = auth_client(user).post(
            reverse("organization-list"),
            {"name": "X", "slug": "taken"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_detail_forbidden_for_non_member(self, auth_client, org_with_roles):
        data = org_with_roles()
        response = auth_client(data["outsider"]).get(org_detail_url(data["org"].id))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_detail_includes_projects(self, auth_client, org_with_roles):
        data = org_with_roles()
        response = auth_client(data["viewer"]).get(org_detail_url(data["org"].id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["projects"]) == 1
        assert response.data["projects"][0]["slug"] == "api"

    def test_patch_org_requires_admin(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = org_detail_url(data["org"].id)
        payload = {"name": "Acme Updated"}

        viewer_resp = auth_client(data["viewer"]).patch(url, payload, format="json")
        assert viewer_resp.status_code == status.HTTP_403_FORBIDDEN

        admin_resp = auth_client(data["admin"]).patch(url, payload, format="json")
        assert admin_resp.status_code == status.HTTP_200_OK
        data["org"].refresh_from_db()
        assert data["org"].name == "Acme Updated"

    def test_delete_org_requires_admin(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = org_detail_url(data["org"].id)
        org_id = data["org"].id

        assert auth_client(data["member"]).delete(url).status_code == status.HTTP_403_FORBIDDEN
        assert auth_client(data["admin"]).delete(url).status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(pk=org_id).exists()


@pytest.mark.django_db
class TestProjectAPI:
    def test_list_projects_viewer_ok(self, auth_client, org_with_roles):
        data = org_with_roles()
        response = auth_client(data["viewer"]).get(project_list_url(data["org"].id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    def test_create_project_requires_admin(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = project_list_url(data["org"].id)
        payload = {"name": "Mobile", "slug": "mobile"}

        assert (
            auth_client(data["member"]).post(url, payload, format="json").status_code
            == status.HTTP_403_FORBIDDEN
        )
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.filter(organization=data["org"], slug="mobile").exists()

    def test_project_detail_wrong_org_returns_404(self, auth_client, org_with_roles):
        data = org_with_roles()
        other_org = OrganizationFactory(slug="other-org")
        OrganizationMembership.objects.create(
            user=data["admin"],
            organization=other_org,
            role=Role.ADMIN,
        )
        url = project_detail_url(other_org.id, data["project"].id)
        assert auth_client(data["admin"]).get(url).status_code == status.HTTP_404_NOT_FOUND

    def test_project_slug_unique_per_org(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = project_list_url(data["org"].id)
        response = auth_client(data["admin"]).post(
            url,
            {"name": "Dup", "slug": "api"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_project_member_forbidden(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = project_detail_url(data["org"].id, data["project"].id)
        payload = {"name": "Renamed"}

        assert (
            auth_client(data["member"]).patch(url, payload, format="json").status_code
            == status.HTTP_403_FORBIDDEN
        )
        assert (
            auth_client(data["admin"]).patch(url, payload, format="json").status_code
            == status.HTTP_200_OK
        )


@pytest.mark.django_db
class TestMembershipAPI:
    def test_list_memberships_viewer_ok(self, auth_client, org_with_roles):
        data = org_with_roles()
        response = auth_client(data["viewer"]).get(membership_list_url(data["org"].id))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_add_member_by_email_requires_admin(self, auth_client, org_with_roles):
        data = org_with_roles()
        new_user = UserFactory(email="new@example.com")
        url = membership_list_url(data["org"].id)
        payload = {"email": new_user.email, "role": Role.MEMBER}

        assert (
            auth_client(data["member"]).post(url, payload, format="json").status_code
            == status.HTTP_403_FORBIDDEN
        )
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMembership.objects.filter(
            user=new_user,
            organization=data["org"],
        ).exists()

    def test_add_member_by_email_case_insensitive(self, auth_client, org_with_roles):
        data = org_with_roles()
        new_user = UserFactory(email="Invitee@Example.com")
        url = membership_list_url(data["org"].id)
        payload = {"email": "invitee@example.com", "role": Role.VIEWER}
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMembership.objects.filter(
            user=new_user,
            organization=data["org"],
            role=Role.VIEWER,
        ).exists()

    def test_add_member_unknown_email_rejected(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = membership_list_url(data["org"].id)
        payload = {"email": "missing@example.com", "role": Role.MEMBER}
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data

    def test_add_member_requires_user_id_or_email(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = membership_list_url(data["org"].id)
        response = auth_client(data["admin"]).post(url, {"role": Role.MEMBER}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_member_rejects_user_id_and_email(self, auth_client, org_with_roles):
        data = org_with_roles()
        new_user = UserFactory(email="both@example.com")
        url = membership_list_url(data["org"].id)
        payload = {
            "user_id": str(new_user.id),
            "email": new_user.email,
            "role": Role.MEMBER,
        }
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_member_requires_admin(self, auth_client, org_with_roles):
        data = org_with_roles()
        new_user = UserFactory(email="new@example.com")
        url = membership_list_url(data["org"].id)
        payload = {"user_id": str(new_user.id), "role": Role.MEMBER}

        assert (
            auth_client(data["member"]).post(url, payload, format="json").status_code
            == status.HTTP_403_FORBIDDEN
        )
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMembership.objects.filter(
            user=new_user,
            organization=data["org"],
        ).exists()

    def test_add_duplicate_member_rejected(self, auth_client, org_with_roles):
        data = org_with_roles()
        url = membership_list_url(data["org"].id)
        payload = {"user_id": str(data["member"].id), "role": Role.VIEWER}
        response = auth_client(data["admin"]).post(url, payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_patch_membership_role_admin_only(self, auth_client, org_with_roles):
        data = org_with_roles()
        membership = OrganizationMembership.objects.get(
            user=data["member"],
            organization=data["org"],
        )
        url = membership_detail_url(data["org"].id, membership.id)
        payload = {"role": Role.VIEWER}

        assert (
            auth_client(data["viewer"]).patch(url, payload, format="json").status_code
            == status.HTTP_403_FORBIDDEN
        )
        response = auth_client(data["admin"]).patch(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        membership.refresh_from_db()
        assert membership.role == Role.VIEWER

    def test_delete_membership_admin_only(self, auth_client, org_with_roles):
        data = org_with_roles()
        membership = OrganizationMembership.objects.get(
            user=data["viewer"],
            organization=data["org"],
        )
        url = membership_detail_url(data["org"].id, membership.id)

        assert auth_client(data["member"]).delete(url).status_code == status.HTTP_403_FORBIDDEN
        assert auth_client(data["admin"]).delete(url).status_code == status.HTTP_204_NO_CONTENT
        assert not OrganizationMembership.objects.filter(pk=membership.id).exists()

    def test_membership_wrong_org_returns_404(self, auth_client, org_with_roles):
        data = org_with_roles()
        membership = OrganizationMembership.objects.get(
            user=data["admin"],
            organization=data["org"],
        )
        fake_org = uuid.uuid4()
        url = membership_detail_url(fake_org, membership.id)
        assert auth_client(data["admin"]).get(url).status_code == status.HTTP_403_FORBIDDEN
