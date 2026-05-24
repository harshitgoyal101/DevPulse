"""Org-scoped build event list API (JWT + RBAC)."""

from django.shortcuts import get_object_or_404
from rest_framework import generics

from apps.ingestion.models import BuildEvent
from apps.ingestion.serializers import BuildEventSerializer
from apps.organizations.mixins import OrgRBACMixin
from apps.organizations.models import Project
from apps.organizations.permissions import HasOrganizationRole


class BuildEventListView(OrgRBACMixin, generics.ListAPIView):
    permission_classes = (HasOrganizationRole,)
    serializer_class = BuildEventSerializer

    def get_queryset(self):
        org_id = self.kwargs["org_id"]
        project_id = self.kwargs["project_id"]
        get_object_or_404(Project, pk=project_id, organization_id=org_id)
        return BuildEvent.objects.filter(project_id=project_id).order_by("-created_at")[:50]
