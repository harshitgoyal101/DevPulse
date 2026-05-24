import { apiFetch } from "./client";
import type {
  CreateMembershipPayload,
  CreateOrganizationPayload,
  CreateProjectPayload,
  Membership,
  Organization,
  OrganizationDetail,
  Project,
  ProjectDetail,
  UpdateMembershipPayload,
  UpdateOrganizationPayload,
  UpdateProjectPayload,
} from "../types/organizations";

export function listOrganizations(token: string): Promise<Organization[]> {
  return apiFetch<Organization[]>("/api/orgs/", { token });
}

export function createOrganization(
  token: string,
  payload: CreateOrganizationPayload,
): Promise<Organization> {
  return apiFetch<Organization>("/api/orgs/", {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getOrganization(token: string, orgId: string): Promise<OrganizationDetail> {
  return apiFetch<OrganizationDetail>(`/api/orgs/${orgId}/`, { token });
}

export function updateOrganization(
  token: string,
  orgId: string,
  payload: UpdateOrganizationPayload,
): Promise<Organization> {
  return apiFetch<Organization>(`/api/orgs/${orgId}/`, {
    token,
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getProject(
  token: string,
  orgId: string,
  projectId: string,
): Promise<ProjectDetail> {
  return apiFetch<ProjectDetail>(`/api/orgs/${orgId}/projects/${projectId}/`, { token });
}

export function createProject(
  token: string,
  orgId: string,
  payload: CreateProjectPayload,
): Promise<Project> {
  return apiFetch<Project>(`/api/orgs/${orgId}/projects/`, {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateProject(
  token: string,
  orgId: string,
  projectId: string,
  payload: UpdateProjectPayload,
): Promise<Project> {
  return apiFetch<Project>(`/api/orgs/${orgId}/projects/${projectId}/`, {
    token,
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteProject(
  token: string,
  orgId: string,
  projectId: string,
): Promise<void> {
  return apiFetch<void>(`/api/orgs/${orgId}/projects/${projectId}/`, {
    token,
    method: "DELETE",
  });
}

export function listMemberships(token: string, orgId: string): Promise<Membership[]> {
  return apiFetch<Membership[]>(`/api/orgs/${orgId}/memberships/`, { token });
}

export function createMembership(
  token: string,
  orgId: string,
  payload: CreateMembershipPayload,
): Promise<Membership> {
  return apiFetch<Membership>(`/api/orgs/${orgId}/memberships/`, {
    token,
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateMembership(
  token: string,
  orgId: string,
  membershipId: string,
  payload: UpdateMembershipPayload,
): Promise<Membership> {
  return apiFetch<Membership>(`/api/orgs/${orgId}/memberships/${membershipId}/`, {
    token,
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteMembership(
  token: string,
  orgId: string,
  membershipId: string,
): Promise<void> {
  return apiFetch<void>(`/api/orgs/${orgId}/memberships/${membershipId}/`, {
    token,
    method: "DELETE",
  });
}
