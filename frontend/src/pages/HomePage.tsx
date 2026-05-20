import { useCallback, useEffect, useState } from "react";
import * as orgApi from "../api/organizations";
import { ProjectsTable } from "../components/ProjectsTable";
import { authErrorMessage, useAuth } from "../context/AuthContext";
import type { Organization, OrganizationDetail } from "../types/organizations";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function MetaItem({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-violet-100 bg-brand-50/50 px-4 py-3">
      <dt className="text-xs font-semibold uppercase tracking-wide text-brand-600">
        {label}
      </dt>
      <dd className="mt-1 text-sm font-medium text-slate-800">{children}</dd>
    </div>
  );
}

export function HomePage() {
  const { user, accessToken, logout } = useAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null);
  const [orgDetail, setOrgDetail] = useState<OrganizationDetail | null>(null);
  const [loadingOrgs, setLoadingOrgs] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadOrganizations = useCallback(async () => {
    if (!accessToken) return;
    setLoadingOrgs(true);
    setError(null);
    try {
      const list = await orgApi.listOrganizations(accessToken);
      setOrganizations(list);
      setSelectedOrgId((current) => {
        if (current && list.some((o) => o.id === current)) return current;
        return list[0]?.id ?? null;
      });
    } catch (err) {
      setError(authErrorMessage(err));
      setOrganizations([]);
      setSelectedOrgId(null);
    } finally {
      setLoadingOrgs(false);
    }
  }, [accessToken]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    if (!accessToken || !selectedOrgId) {
      setOrgDetail(null);
      return;
    }

    let cancelled = false;
    setLoadingDetail(true);
    setError(null);

    orgApi
      .getOrganization(accessToken, selectedOrgId)
      .then((detail) => {
        if (!cancelled) setOrgDetail(detail);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(authErrorMessage(err));
          setOrgDetail(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingDetail(false);
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken, selectedOrgId]);

  const displayName =
    user && [user.first_name, user.last_name].filter(Boolean).join(" ");

  const initials = displayName
    ? displayName
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
        .toUpperCase()
    : user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 via-white to-white">
      <header className="sticky top-0 z-10 border-b border-violet-100 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold text-white shadow-md shadow-brand-600/30">
              DP
            </div>
            <div>
              <h1 className="text-lg font-bold text-brand-900">DevPulse</h1>
              <p className="text-xs text-slate-500">CI/CD observability</p>
            </div>
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-slate-800">
                {displayName || user?.email}
              </p>
              {displayName && (
                <p className="text-xs text-slate-500">{user?.email}</p>
              )}
            </div>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700 sm:hidden">
              {initials}
            </div>
            <button type="button" className="btn-secondary" onClick={() => logout()}>
              Log out
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-6 px-4 py-8 sm:px-6">
        {error && (
          <div
            className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
            role="alert"
          >
            {error}
          </div>
        )}

        <section className="card-surface">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-brand-900">Organization</h2>
              <p className="mt-0.5 text-sm text-slate-500">
                Tenant details and membership scope
              </p>
            </div>
            {organizations.length > 1 && (
              <label className="flex flex-col gap-1 sm:items-end">
                <span className="text-xs font-medium text-brand-700">
                  Switch organization
                </span>
                <select
                  className="input-field min-w-[12rem] sm:max-w-xs"
                  value={selectedOrgId ?? ""}
                  onChange={(e) => setSelectedOrgId(e.target.value || null)}
                  disabled={loadingOrgs}
                >
                  {organizations.map((org) => (
                    <option key={org.id} value={org.id}>
                      {org.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>

          {loadingOrgs && (
            <p className="mt-6 text-sm text-slate-500">Loading organizations…</p>
          )}

          {!loadingOrgs && organizations.length === 0 && (
            <p className="mt-6 rounded-xl bg-brand-50 px-4 py-8 text-center text-sm text-slate-600">
              You are not a member of any organization yet.
            </p>
          )}

          {!loadingOrgs && orgDetail && (
            <dl className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <MetaItem label="Name">{orgDetail.name}</MetaItem>
              <MetaItem label="Slug">
                <code className="rounded-md bg-white px-2 py-0.5 font-mono text-xs text-brand-700 ring-1 ring-violet-100">
                  {orgDetail.slug}
                </code>
              </MetaItem>
              <MetaItem label="Projects">{orgDetail.projects.length}</MetaItem>
              <MetaItem label="Created">{formatDate(orgDetail.created_at)}</MetaItem>
              <MetaItem label="Updated">{formatDate(orgDetail.updated_at)}</MetaItem>
              <MetaItem label="Organization ID">
                <code className="break-all font-mono text-xs text-slate-600">
                  {orgDetail.id}
                </code>
              </MetaItem>
            </dl>
          )}

          {!loadingOrgs && selectedOrgId && loadingDetail && (
            <p className="mt-6 text-sm text-slate-500">Loading organization details…</p>
          )}
        </section>

        <section className="card-surface overflow-hidden p-0">
          <div className="border-b border-violet-100 bg-gradient-to-r from-brand-600 to-brand-700 px-6 py-4">
            <h2 className="text-lg font-semibold text-white">Projects</h2>
            <p className="mt-0.5 text-sm text-violet-100">
              {orgDetail
                ? `${orgDetail.projects.length} project${orgDetail.projects.length === 1 ? "" : "s"} in ${orgDetail.name}`
                : "Build targets within the selected organization"}
            </p>
          </div>
          <div className="p-6">
            {orgDetail && !loadingDetail ? (
              <ProjectsTable projects={orgDetail.projects} />
            ) : (
              !loadingOrgs &&
              selectedOrgId &&
              loadingDetail && (
                <p className="text-sm text-slate-500">Loading projects…</p>
              )
            )}
            {!loadingOrgs && !selectedOrgId && (
              <p className="text-center text-sm text-slate-500">
                Select an organization to view projects.
              </p>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
