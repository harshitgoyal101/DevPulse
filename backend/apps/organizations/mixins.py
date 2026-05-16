"""Queryset scoping and RBAC helpers for org-scoped API views."""

from apps.organizations.permissions import get_user_organizations

from .models import Role


class UserOrganizationsQuerysetMixin:
    """Restrict queryset to organizations the current user belongs to."""

    def get_queryset(self):
        return get_user_organizations(self.request.user)


class OrgScopedQuerysetMixin:
    """Filter queryset to the organization identified in the URL."""

    org_url_kwarg = "org_id"

    def get_org_id(self):
        return self.kwargs[self.org_url_kwarg]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization_id=self.get_org_id())


class OrgRBACMixin:
    """
    Set ``required_org_role`` before permission checks based on HTTP method.

    Works with ``HasOrganizationRole`` on org-scoped routes (``org_id`` in URL).
    """

    read_methods = ("GET", "HEAD", "OPTIONS")
    read_org_role = Role.VIEWER
    write_org_role = Role.ADMIN

    def get_required_org_role(self):
        if self.request.method in self.read_methods:
            return self.read_org_role
        return self.write_org_role

    def check_permissions(self, request):
        self.required_org_role = self.get_required_org_role()
        return super().check_permissions(request)
