import { apiFetch } from "./client";
import type { BuildEvent } from "../types/builds";

export function listBuildEvents(
  token: string,
  orgId: string,
  projectId: string,
): Promise<BuildEvent[]> {
  return apiFetch<BuildEvent[]>(
    `/api/orgs/${orgId}/projects/${projectId}/builds/`,
    { token },
  );
}
