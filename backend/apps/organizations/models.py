"""Organizations, projects, and membership roles (RBAC data model)."""

import uuid

from django.conf import settings
from django.db import models


class Role(models.TextChoices):
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    VIEWER = "viewer", "Viewer"


ROLE_RANK = {
    Role.ADMIN: 3,
    Role.MEMBER: 2,
    Role.VIEWER: 1,
}


class Organization(models.Model):
    """
    Top-level tenant. Users belong via OrganizationMembership.

    Roles (enforced at API layer in later milestones):

    - admin: manage members, projects, alert rules.
    - member: view builds, configure personal notifications.
    - viewer: read-only access to org projects.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    """Builds and webhooks attach to a project within an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "slug"),
                name="organizations_project_organization_slug_unique",
            ),
        ]
        ordering = ("organization_id", "name")

    def __str__(self) -> str:
        return f"{self.organization.slug}/{self.slug}"


class OrganizationMembership(models.Model):
    """Maps a user to an organization with exactly one role."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(
        max_length=32,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "organization"),
                name="organizations_membership_user_org_unique",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}@{self.organization_id} ({self.role})"
