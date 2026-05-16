"""
Queryset scoping mixins (org isolation for list/detail views in later milestones).

When build and project APIs land, use a mixin that restricts querysets to
organizations the current user belongs to, and apply `HasOrganizationRole`
on mutating actions.
"""


class OrgScopedQuerysetMixin:
    """
    Example pattern for later development:

    ```python
    def get_queryset(self):
        qs = super().get_queryset()
        org_ids = OrganizationMembership.objects.filter(
            user=self.request.user
        ).values_list(\"organization_id\", flat=True)
        return qs.filter(organization_id__in=org_ids)
    ```
    """
