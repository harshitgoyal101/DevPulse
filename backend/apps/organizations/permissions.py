"""RBAC helpers for org-scoped API views."""

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet
from rest_framework.permissions import BasePermission

from .models import ROLE_RANK, Organization, OrganizationMembership, Role


def get_user_organizations(user: AbstractBaseUser) -> QuerySet[Organization]:
    """Organizations the user belongs to (any role)."""
    if not user.is_authenticated:
        return Organization.objects.none()
    return Organization.objects.filter(memberships__user_id=user.pk).distinct()


def get_user_role(user: AbstractBaseUser, org_id) -> str | None:
    """Return role string for user in org, or None if not a member."""
    if not user.is_authenticated:
        return None
    row = (
        OrganizationMembership.objects.filter(user_id=user.pk, organization_id=org_id)
        .values_list("role", flat=True)
        .first()
    )
    return row


class IsOrganizationMember(BasePermission):
    """
    True when URL kwargs include `org_id` and the user has membership in that org.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user.is_authenticated:
            return False
        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False
        return OrganizationMembership.objects.filter(
            user_id=user.pk,
            organization_id=org_id,
        ).exists()


class HasOrganizationRole(BasePermission):
    """
    Require membership with at least `required_org_role` (default VIEWER).

    Set on the view: ``required_org_role = Role.MEMBER``.
    """

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user.is_authenticated:
            return False
        org_id = view.kwargs.get("org_id")
        if not org_id:
            return False
        required = getattr(view, "required_org_role", Role.VIEWER)
        if required not in ROLE_RANK:
            return False
        role = get_user_role(user, org_id)
        if role is None or role not in ROLE_RANK:
            return False
        return ROLE_RANK[role] >= ROLE_RANK[required]
