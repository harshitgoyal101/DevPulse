import type { Role } from "../types/organizations";

const ROLE_RANK: Record<Role, number> = {
  viewer: 1,
  member: 2,
  admin: 3,
};

export function hasMinimumRole(userRole: Role | null, required: Role): boolean {
  if (!userRole) return false;
  return ROLE_RANK[userRole] >= ROLE_RANK[required];
}

export function formatRole(role: Role): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}
