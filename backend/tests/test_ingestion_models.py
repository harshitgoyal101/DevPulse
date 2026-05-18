import pytest
from django.db import IntegrityError

from apps.ingestion.models import BuildEvent, BuildStatus, WebhookDelivery, WebhookProvider
from tests.factories import ProjectFactory


@pytest.mark.django_db
def test_webhook_delivery_unique_per_provider_delivery_id():
    project = ProjectFactory()
    WebhookDelivery.objects.create(
        project=project,
        provider=WebhookProvider.GITHUB,
        delivery_id="abc-123",
    )
    with pytest.raises(IntegrityError):
        WebhookDelivery.objects.create(
            project=project,
            provider=WebhookProvider.GITHUB,
            delivery_id="abc-123",
        )


@pytest.mark.django_db
def test_webhook_delivery_same_delivery_id_different_provider_allowed():
    project = ProjectFactory()
    WebhookDelivery.objects.create(
        project=project,
        provider=WebhookProvider.GITHUB,
        delivery_id="shared-id",
    )
    WebhookDelivery.objects.create(
        project=project,
        provider=WebhookProvider.GITLAB,
        delivery_id="shared-id",
    )
    assert WebhookDelivery.objects.filter(project=project).count() == 2


@pytest.mark.django_db
def test_webhook_delivery_cascade_delete_with_project():
    project = ProjectFactory()
    WebhookDelivery.objects.create(
        project=project,
        provider=WebhookProvider.GITHUB,
        delivery_id="del-1",
    )
    project_id = project.id
    project.delete()
    assert not WebhookDelivery.objects.filter(project_id=project_id).exists()


@pytest.mark.django_db
def test_build_event_persists_fields_and_indexes():
    project = ProjectFactory()
    payload = {"workflow_run": {"id": 42, "conclusion": "success"}}
    event = BuildEvent.objects.create(
        project=project,
        status=BuildStatus.SUCCESS,
        branch="main",
        commit_sha="a" * 40,
        duration=120,
        raw_payload=payload,
    )
    event.refresh_from_db()
    assert event.project_id == project.id
    assert event.status == BuildStatus.SUCCESS
    assert event.branch == "main"
    assert event.commit_sha == "a" * 40
    assert event.duration == 120
    assert event.raw_payload == payload
    assert event.created_at is not None

    index_fields = {tuple(index.fields) for index in BuildEvent._meta.indexes}
    assert ("project", "created_at") in index_fields
    assert ("status", "branch") in index_fields


@pytest.mark.django_db
def test_build_event_cascade_delete_with_project():
    project = ProjectFactory()
    BuildEvent.objects.create(
        project=project,
        status=BuildStatus.FAILURE,
        branch="feature/x",
        commit_sha="b" * 40,
        raw_payload={},
    )
    project_id = project.id
    project.delete()
    assert not BuildEvent.objects.filter(project_id=project_id).exists()
