import hashlib
import hmac
import json
import uuid

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.ingestion.models import BuildEvent, WebhookDelivery, WebhookProvider
from apps.organizations.models import OrganizationMembership, Project, Role
from tests.factories import OrganizationFactory, ProjectFactory, UserFactory


def webhook_url(provider: str, project_id) -> str:
    return reverse("webhook-receive", kwargs={"provider": provider, "project_id": project_id})


def github_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


GITHUB_WORKFLOW_PAYLOAD = {
    "action": "completed",
    "workflow_run": {
        "head_branch": "main",
        "head_sha": "a" * 40,
        "status": "completed",
        "conclusion": "success",
        "run_started_at": "2026-05-01T10:00:00Z",
        "updated_at": "2026-05-01T10:05:00Z",
    },
}

GITLAB_PIPELINE_PAYLOAD = {
    "object_attributes": {
        "ref": "main",
        "sha": "b" * 40,
        "status": "success",
        "duration": 120,
    },
}


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
    viewer = UserFactory(email="viewer@example.com")
    OrganizationMembership.objects.create(user=admin, organization=org, role=Role.ADMIN)
    OrganizationMembership.objects.create(user=viewer, organization=org, role=Role.VIEWER)
    project = Project.objects.create(
        organization=org,
        name="API",
        slug="api",
        webhook_secret="admin-visible-secret",
    )
    return {"org": org, "admin": admin, "viewer": viewer, "project": project}


@pytest.fixture
def project():
    return ProjectFactory(
        webhook_secret="test-webhook-secret",
        slug="api",
    )


@pytest.mark.django_db
class TestWebhookReceive:
    def test_invalid_github_signature_returns_401(self, project):
        body = json.dumps(GITHUB_WORKFLOW_PAYLOAD).encode()
        client = APIClient()
        response = client.post(
            webhook_url(WebhookProvider.GITHUB, project.id),
            data=body,
            content_type="application/json",
            HTTP_X_GITHUB_DELIVERY="delivery-401",
            HTTP_X_HUB_SIGNATURE_256="sha256=invalid",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert not WebhookDelivery.objects.exists()

    def test_unknown_project_returns_404(self, project):
        body = json.dumps(GITHUB_WORKFLOW_PAYLOAD).encode()
        client = APIClient()
        fake_id = uuid.uuid4()
        response = client.post(
            webhook_url(WebhookProvider.GITHUB, fake_id),
            data=body,
            content_type="application/json",
            HTTP_X_GITHUB_DELIVERY="delivery-404",
            HTTP_X_HUB_SIGNATURE_256=github_signature(project.webhook_secret, body),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_valid_github_webhook_creates_delivery_and_build(self, project):
        body = json.dumps(GITHUB_WORKFLOW_PAYLOAD).encode()
        delivery_id = "github-delivery-happy-1"
        client = APIClient()
        response = client.post(
            webhook_url(WebhookProvider.GITHUB, project.id),
            data=body,
            content_type="application/json",
            HTTP_X_GITHUB_DELIVERY=delivery_id,
            HTTP_X_HUB_SIGNATURE_256=github_signature(project.webhook_secret, body),
        )
        assert response.status_code == status.HTTP_202_ACCEPTED

        delivery = WebhookDelivery.objects.get(
            provider=WebhookProvider.GITHUB,
            delivery_id=delivery_id,
        )
        assert delivery.project_id == project.id
        assert delivery.raw_payload == GITHUB_WORKFLOW_PAYLOAD

        build = BuildEvent.objects.get(webhook_delivery=delivery)
        assert build.project_id == project.id
        assert build.status == "success"
        assert build.branch == "main"
        assert build.commit_sha == "a" * 40
        assert build.duration == 300

    def test_duplicate_delivery_returns_202_without_second_build(self, project):
        body = json.dumps(GITHUB_WORKFLOW_PAYLOAD).encode()
        delivery_id = "github-delivery-dedup"
        url = webhook_url(WebhookProvider.GITHUB, project.id)
        headers = {
            "HTTP_X_GITHUB_DELIVERY": delivery_id,
            "HTTP_X_HUB_SIGNATURE_256": github_signature(project.webhook_secret, body),
        }
        client = APIClient()

        assert client.post(url, data=body, content_type="application/json", **headers).status_code == 202
        assert BuildEvent.objects.filter(webhook_delivery__delivery_id=delivery_id).count() == 1

        assert client.post(url, data=body, content_type="application/json", **headers).status_code == 202
        assert BuildEvent.objects.filter(webhook_delivery__delivery_id=delivery_id).count() == 1

    def test_valid_gitlab_webhook_creates_build(self, project):
        body = json.dumps(GITLAB_PIPELINE_PAYLOAD).encode()
        delivery_id = "gitlab-delivery-happy-1"
        client = APIClient()
        response = client.post(
            webhook_url(WebhookProvider.GITLAB, project.id),
            data=body,
            content_type="application/json",
            HTTP_X_GITLAB_EVENT_UUID=delivery_id,
            HTTP_X_GITLAB_TOKEN=project.webhook_secret,
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        delivery = WebhookDelivery.objects.get(
            provider=WebhookProvider.GITLAB,
            delivery_id=delivery_id,
        )
        build = BuildEvent.objects.get(webhook_delivery=delivery)
        assert build.status == "success"
        assert build.duration == 120


@pytest.mark.django_db
class TestProjectWebhookSecretAPI:
    def test_admin_sees_webhook_secret_on_project_detail(self, auth_client, org_with_roles):
        data = org_with_roles
        url = reverse(
            "project-detail",
            kwargs={"org_id": data["org"].id, "project_id": data["project"].id},
        )
        admin_resp = auth_client(data["admin"]).get(url)
        assert admin_resp.status_code == status.HTTP_200_OK
        assert "webhook_secret" in admin_resp.data
        assert admin_resp.data["webhook_secret"] == "admin-visible-secret"

        viewer_resp = auth_client(data["viewer"]).get(url)
        assert viewer_resp.status_code == status.HTTP_200_OK
        assert "webhook_secret" not in viewer_resp.data

        list_resp = auth_client(data["admin"]).get(
            reverse("project-list", kwargs={"org_id": data["org"].id}),
        )
        assert "webhook_secret" not in list_resp.data[0]
