import { apiFetch } from "./client";
import type { Organization, OrganizationDetail } from "../types/organizations";

export function listOrganizations(token: string): Promise<Organization[]> {
  return apiFetch<Organization[]>("/api/orgs/", { token });
}

export function getOrganization(token: string, orgId: string): Promise<OrganizationDetail> {
  return apiFetch<OrganizationDetail>(`/api/orgs/${orgId}/`, { token });
}
