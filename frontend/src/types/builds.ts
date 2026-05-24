export type BuildStatus =
  | "pending"
  | "success"
  | "failure"
  | "cancelled"
  | "skipped";

export interface BuildEvent {
  id: string;
  status: BuildStatus;
  branch: string;
  commit_sha: string;
  duration: number | null;
  created_at: string;
}
