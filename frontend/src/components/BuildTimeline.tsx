import type { BuildEvent, BuildStatus } from "../types/builds";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatDuration(seconds: number | null): string {
  if (seconds == null) return "—";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return remainder > 0 ? `${minutes}m ${remainder}s` : `${minutes}m`;
}

function shortSha(sha: string): string {
  return sha.length > 7 ? sha.slice(0, 7) : sha;
}

const STATUS_STYLES: Record<BuildStatus, string> = {
  pending: "bg-amber-100 text-amber-800 ring-amber-200",
  success: "bg-emerald-100 text-emerald-800 ring-emerald-200",
  failure: "bg-red-100 text-red-800 ring-red-200",
  cancelled: "bg-slate-100 text-slate-700 ring-slate-200",
  skipped: "bg-violet-100 text-violet-800 ring-violet-200",
};

function StatusChip({ status }: { status: BuildStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {status}
    </span>
  );
}

interface BuildTimelineProps {
  builds: BuildEvent[];
  loading?: boolean;
}

export function BuildTimeline({ builds, loading = false }: BuildTimelineProps) {
  if (loading) {
    return <p className="text-sm text-slate-500">Loading builds…</p>;
  }

  if (builds.length === 0) {
    return (
      <p className="rounded-xl bg-brand-50 px-4 py-8 text-center text-sm text-slate-600">
        No builds yet. Send a webhook or run{" "}
        <code className="rounded bg-white px-1.5 py-0.5 font-mono text-xs text-brand-700 ring-1 ring-violet-100">
          simulate_webhook
        </code>{" "}
        to create one.
      </p>
    );
  }

  return (
    <div className="-mx-2 overflow-x-auto sm:mx-0">
      <table className="w-full min-w-[520px] border-separate border-spacing-0 text-sm">
        <thead>
          <tr>
            <th className="border-b border-violet-100 bg-brand-50/80 px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-brand-700 first:rounded-tl-lg">
              Status
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Branch
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Commit
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Duration
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-brand-700 last:rounded-tr-lg">
              Created
            </th>
          </tr>
        </thead>
        <tbody>
          {builds.map((build, index) => (
            <tr key={build.id} className="transition hover:bg-brand-50/60">
              <td
                className={`border-b border-violet-50 px-3 py-3 ${
                  index === builds.length - 1 ? "rounded-bl-lg border-b-0" : ""
                }`}
              >
                <StatusChip status={build.status} />
              </td>
              <td
                className={`border-b border-violet-50 px-3 py-3 font-medium text-slate-800 ${
                  index === builds.length - 1 ? "border-b-0" : ""
                }`}
              >
                {build.branch}
              </td>
              <td
                className={`border-b border-violet-50 px-3 py-3 ${
                  index === builds.length - 1 ? "border-b-0" : ""
                }`}
              >
                <code className="rounded-md bg-violet-50 px-2 py-0.5 font-mono text-xs text-brand-700">
                  {shortSha(build.commit_sha)}
                </code>
              </td>
              <td
                className={`border-b border-violet-50 px-3 py-3 text-slate-600 ${
                  index === builds.length - 1 ? "border-b-0" : ""
                }`}
              >
                {formatDuration(build.duration)}
              </td>
              <td
                className={`border-b border-violet-50 px-3 py-3 text-slate-600 ${
                  index === builds.length - 1 ? "rounded-br-lg border-b-0" : ""
                }`}
              >
                {formatDate(build.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
