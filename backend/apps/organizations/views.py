from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .mixins import OrgRBACMixin, OrgScopedQuerysetMixin, UserOrganizationsQuerysetMixin
from .models import Organization, OrganizationMembership, Project
from .permissions import HasOrganizationRole
from .serializers import (
    MembershipCreateSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    OrganizationCreateSerializer,
    OrganizationDetailSerializer,
    OrganizationSerializer,
    ProjectSerializer,
)


class OrganizationListCreateView(
    UserOrganizationsQuerysetMixin,
    generics.ListCreateAPIView,
):
    permission_classes = (IsAuthenticated,)
    queryset = Organization.objects.all()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrganizationCreateSerializer
        return OrganizationSerializer


class OrganizationDetailView(
    OrgRBACMixin,
    UserOrganizationsQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    permission_classes = (HasOrganizationRole,)
    queryset = Organization.objects.all()
    lookup_url_kwarg = "org_id"

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrganizationDetailSerializer
        return OrganizationSerializer


class ProjectListCreateView(
    OrgRBACMixin,
    OrgScopedQuerysetMixin,
    generics.ListCreateAPIView,
):
    permission_classes = (HasOrganizationRole,)
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_id"] = self.get_org_id()
        return context

    def perform_create(self, serializer):
        serializer.save(organization_id=self.get_org_id())


class ProjectDetailView(
    OrgRBACMixin,
    OrgScopedQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    permission_classes = (HasOrganizationRole,)
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_url_kwarg = "project_id"

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_id"] = self.get_org_id()
        return context


class MembershipListCreateView(
    OrgRBACMixin,
    OrgScopedQuerysetMixin,
    generics.ListCreateAPIView,
):
    permission_classes = (HasOrganizationRole,)
    queryset = OrganizationMembership.objects.select_related("user")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return MembershipCreateSerializer
        return MembershipSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["org_id"] = self.get_org_id()
        return context


class MembershipDetailView(
    OrgRBACMixin,
    OrgScopedQuerysetMixin,
    generics.RetrieveUpdateDestroyAPIView,
):
    permission_classes = (HasOrganizationRole,)
    queryset = OrganizationMembership.objects.select_related("user")
    lookup_url_kwarg = "membership_id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return MembershipUpdateSerializer
        return MembershipSerializer
