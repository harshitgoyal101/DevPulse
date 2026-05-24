export type Role = "admin" | "member" | "viewer";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  webhook_secret?: string;
}

export interface OrganizationDetail extends Organization {
  projects: Project[];
}

export interface Membership {
  id: string;
  user_id: string;
  email: string;
  role: Role;
  created_at: string;
}

export interface CreateOrganizationPayload {
  name: string;
  slug: string;
}

export interface UpdateOrganizationPayload {
  name?: string;
  slug?: string;
}

export interface CreateProjectPayload {
  name: string;
  slug: string;
}

export interface UpdateProjectPayload {
  name?: string;
  slug?: string;
}

export interface CreateMembershipPayload {
  user_id?: string;
  email?: string;
  role: Role;
}

export interface UpdateMembershipPayload {
  role: Role;
}
