import { useCallback, useState } from "react";
import {
  formatWebhookProvider,
  webhookProviders,
  webhookUrl,
} from "../lib/webhook";
import type { BuildEvent } from "../types/builds";
import type { ProjectDetail } from "../types/organizations";
import { BuildTimeline } from "./BuildTimeline";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }, [value]);

  return (
    <button
      type="button"
      className="btn-secondary shrink-0 px-3 py-1.5 text-xs"
      onClick={() => void handleCopy()}
    >
      {copied ? "Copied!" : `Copy ${label}`}
    </button>
  );
}

interface ProjectDetailPanelProps {
  project: ProjectDetail | null;
  builds: BuildEvent[];
  loading: boolean;
  isAdmin: boolean;
  orgSlug?: string;
  onRefresh?: () => void;
}

export function ProjectDetailPanel({
  project,
  builds,
  loading,
  isAdmin,
  orgSlug,
  onRefresh,
}: ProjectDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "webhook" | "builds">("overview");

  if (loading && !project) {
    return (
      <div className="card-surface">
        <p className="text-sm text-slate-500">Loading project details…</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="card-surface">
        <p className="text-center text-sm text-slate-500">
          Select a project to view details, webhook setup, and recent builds.
        </p>
      </div>
    );
  }

  const tabs = [
    { id: "overview" as const, label: "Overview" },
    { id: "webhook" as const, label: "Webhook setup" },
    { id: "builds" as const, label: "Recent builds" },
  ];

  return (
    <div className="card-surface overflow-hidden p-0">
      <div className="border-b border-violet-100 bg-gradient-to-r from-brand-600 to-brand-700 px-6 py-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">{project.name}</h2>
            <p className="mt-0.5 text-sm text-violet-100">
              <code className="font-mono">{project.slug}</code>
            </p>
          </div>
          {onRefresh && (
            <button
              type="button"
              className="btn-secondary border-white/30 bg-white/10 text-white hover:bg-white/20"
              onClick={onRefresh}
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      <div className="border-b border-violet-100 px-4 pt-3">
        <nav className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={`whitespace-nowrap rounded-t-lg px-4 py-2 text-sm font-medium transition ${
                activeTab === tab.id
                  ? "bg-white text-brand-700 shadow-sm ring-1 ring-violet-100"
                  : "text-slate-600 hover:bg-brand-50 hover:text-brand-700"
              }`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="p-6">
        {activeTab === "overview" && (
          <dl className="grid gap-3 sm:grid-cols-2">
            <MetaItem label="Project ID">
              <code className="break-all font-mono text-xs text-slate-600">{project.id}</code>
            </MetaItem>
            <MetaItem label="Slug">
              <code className="rounded-md bg-violet-50 px-2 py-0.5 font-mono text-xs text-brand-700">
                {project.slug}
              </code>
            </MetaItem>
            <MetaItem label="Created">{formatDate(project.created_at)}</MetaItem>
            <MetaItem label="Updated">{formatDate(project.updated_at)}</MetaItem>
          </dl>
        )}

        {activeTab === "webhook" && (
          <div className="space-y-4">
            {isAdmin ? (
              <>
                {webhookProviders().map((provider) => (
                  <div
                    key={provider}
                    className="rounded-xl border border-violet-100 bg-brand-50/40 p-4"
                  >
                    <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">
                      {formatWebhookProvider(provider)}
                    </p>
                    <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
                      <code className="flex-1 break-all rounded-lg bg-white px-3 py-2 font-mono text-xs text-slate-700 ring-1 ring-violet-100">
                        POST {webhookUrl(provider, project.id)}
                      </code>
                      <CopyButton value={webhookUrl(provider, project.id)} label="URL" />
                    </div>
                  </div>
                ))}
                {project.webhook_secret && (
                  <div className="rounded-xl border border-violet-100 bg-brand-50/40 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">
                      Webhook secret
                    </p>
                    <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
                      <code className="flex-1 break-all rounded-lg bg-white px-3 py-2 font-mono text-xs text-slate-700 ring-1 ring-violet-100">
                        {project.webhook_secret}
                      </code>
                      <CopyButton value={project.webhook_secret} label="secret" />
                    </div>
                  </div>
                )}
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <code className="flex-1 break-all rounded-lg bg-white px-3 py-2 font-mono text-xs text-slate-700 ring-1 ring-violet-100">
                    {project.id}
                  </code>
                  <CopyButton value={project.id} label="project ID" />
                </div>
                <p className="text-sm text-slate-600">
                  Test locally with{" "}
                  <code className="rounded bg-violet-50 px-1.5 py-0.5 font-mono text-xs text-brand-700">
                    python manage.py simulate_webhook --org-slug {orgSlug ?? "acme"} --project-slug{" "}
                    {project.slug}
                  </code>
                </p>
              </>
            ) : (
              <p className="text-sm text-slate-600">
                Webhook URLs and secrets are visible to organization admins only.
              </p>
            )}
          </div>
        )}

        {activeTab === "builds" && <BuildTimeline builds={builds} loading={loading} />}
      </div>
    </div>
  );
}

function MetaItem({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-violet-100 bg-brand-50/50 px-4 py-3">
      <dt className="text-xs font-semibold uppercase tracking-wide text-brand-600">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-slate-800">{children}</dd>
    </div>
  );
}
