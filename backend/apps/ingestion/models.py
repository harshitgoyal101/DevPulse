"""Webhook deduplication and parsed CI build events."""

import uuid

from django.db import models

from apps.organizations.models import Project


class WebhookProvider(models.TextChoices):
    GITHUB = "github", "GitHub"
    GITLAB = "gitlab", "GitLab"


class BuildStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"
    CANCELLED = "cancelled", "Cancelled"
    SKIPPED = "skipped", "Skipped"


class WebhookDelivery(models.Model):
    """
    One row per provider delivery ID (dedup before async processing).

    Unique on (provider, delivery_id) so duplicate webhook posts are idempotent.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="webhook_deliveries",
    )
    provider = models.CharField(max_length=32, choices=WebhookProvider.choices)
    delivery_id = models.CharField(max_length=255)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("provider", "delivery_id"),
                name="ingestion_webhookdelivery_provider_delivery_id_unique",
            ),
        ]
        ordering = ("-received_at",)

    def __str__(self) -> str:
        return f"{self.provider}:{self.delivery_id}"


class BuildEvent(models.Model):
    """Normalized build/run record parsed from a webhook payload."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="build_events",
    )
    status = models.CharField(max_length=32, choices=BuildStatus.choices)
    branch = models.CharField(max_length=255)
    commit_sha = models.CharField(max_length=64)
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Build duration in seconds, when known.",
    )
    raw_payload = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["project", "created_at"]),
            models.Index(fields=["status", "branch"]),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.project_id} {self.status} {self.branch}@{self.commit_sha[:7]}"
