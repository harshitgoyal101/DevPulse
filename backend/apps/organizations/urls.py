from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrganizationListCreateView.as_view(), name="organization-list"),
    path("<uuid:org_id>/", views.OrganizationDetailView.as_view(), name="organization-detail"),
    path(
        "<uuid:org_id>/projects/",
        views.ProjectListCreateView.as_view(),
        name="project-list",
    ),
    path(
        "<uuid:org_id>/projects/<uuid:project_id>/",
        views.ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "<uuid:org_id>/memberships/",
        views.MembershipListCreateView.as_view(),
        name="membership-list",
    ),
    path(
        "<uuid:org_id>/memberships/<uuid:membership_id>/",
        views.MembershipDetailView.as_view(),
        name="membership-detail",
    ),
]
