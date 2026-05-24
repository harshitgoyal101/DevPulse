import { useCallback, useEffect, useState } from "react";
import * as buildsApi from "../api/builds";
import * as orgApi from "../api/organizations";
import { AddMemberForm } from "../components/AddMemberForm";
import { CreateOrganizationForm } from "../components/CreateOrganizationForm";
import { CreateProjectForm } from "../components/CreateProjectForm";
import { EditOrganizationForm } from "../components/EditOrganizationForm";
import { MembersTable } from "../components/MembersTable";
import { ProjectDetailPanel } from "../components/ProjectDetailPanel";
import { ProjectsTable } from "../components/ProjectsTable";
import { authErrorMessage, useAuth } from "../context/AuthContext";
import { useOrgMembership } from "../hooks/useOrgMembership";
import { formatRole, hasMinimumRole } from "../lib/roles";
import type { BuildEvent } from "../types/builds";
import type {
  Membership,
  Organization,
  OrganizationDetail,
  ProjectDetail,
  Role,
} from "../types/organizations";

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
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [projectDetail, setProjectDetail] = useState<ProjectDetail | null>(null);
  const [builds, setBuilds] = useState<BuildEvent[]>([]);
  const [loadingOrgs, setLoadingOrgs] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [loadingProject, setLoadingProject] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateOrg, setShowCreateOrg] = useState(false);
  const [showEditOrg, setShowEditOrg] = useState(false);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);

  const { role, loading: loadingRole, refetch: refetchMembership } = useOrgMembership(
    accessToken,
    selectedOrgId,
    user?.email,
  );
  const isAdmin = hasMinimumRole(role, "admin");

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

  const loadOrgDetail = useCallback(async () => {
    if (!accessToken || !selectedOrgId) {
      setOrgDetail(null);
      return;
    }
    setLoadingDetail(true);
    try {
      const detail = await orgApi.getOrganization(accessToken, selectedOrgId);
      setOrgDetail(detail);
      setSelectedProjectId((current) => {
        if (current && detail.projects.some((p) => p.id === current)) return current;
        return null;
      });
    } catch (err) {
      setError(authErrorMessage(err));
      setOrgDetail(null);
    } finally {
      setLoadingDetail(false);
    }
  }, [accessToken, selectedOrgId]);

  const loadMembers = useCallback(async () => {
    if (!accessToken || !selectedOrgId) {
      setMemberships([]);
      return;
    }
    setLoadingMembers(true);
    try {
      const list = await orgApi.listMemberships(accessToken, selectedOrgId);
      setMemberships(list);
    } catch (err) {
      setError(authErrorMessage(err));
      setMemberships([]);
    } finally {
      setLoadingMembers(false);
    }
  }, [accessToken, selectedOrgId]);

  const loadProjectData = useCallback(
    async (projectId: string) => {
      if (!accessToken || !selectedOrgId) return;
      setLoadingProject(true);
      try {
        const [detail, buildList] = await Promise.all([
          orgApi.getProject(accessToken, selectedOrgId, projectId),
          buildsApi.listBuildEvents(accessToken, selectedOrgId, projectId),
        ]);
        setProjectDetail(detail);
        setBuilds(buildList);
      } catch (err) {
        setError(authErrorMessage(err));
        setProjectDetail(null);
        setBuilds([]);
      } finally {
        setLoadingProject(false);
      }
    },
    [accessToken, selectedOrgId],
  );

  useEffect(() => {
    void loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    void loadOrgDetail();
  }, [loadOrgDetail]);

  useEffect(() => {
    void loadMembers();
  }, [loadMembers]);

  useEffect(() => {
    if (selectedProjectId) {
      void loadProjectData(selectedProjectId);
    } else {
      setProjectDetail(null);
      setBuilds([]);
    }
  }, [selectedProjectId, loadProjectData]);

  const handleCreateOrg = async (payload: { name: string; slug: string }) => {
    if (!accessToken) return;
    const org = await orgApi.createOrganization(accessToken, payload);
    setShowCreateOrg(false);
    await loadOrganizations();
    setSelectedOrgId(org.id);
  };

  const handleCreateProject = async (payload: { name: string; slug: string }) => {
    if (!accessToken || !selectedOrgId) return;
    await orgApi.createProject(accessToken, selectedOrgId, payload);
    setShowCreateProject(false);
    await loadOrgDetail();
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!accessToken || !selectedOrgId) return;
    await orgApi.deleteProject(accessToken, selectedOrgId, projectId);
    if (selectedProjectId === projectId) {
      setSelectedProjectId(null);
    }
    await loadOrgDetail();
  };

  const handleAddMember = async (payload: { email: string; role: Role }) => {
    if (!accessToken || !selectedOrgId) return;
    await orgApi.createMembership(accessToken, selectedOrgId, payload);
    setShowAddMember(false);
    await Promise.all([loadMembers(), refetchMembership()]);
  };

  const handleUpdateOrg = async (payload: { name: string; slug: string }) => {
    if (!accessToken || !selectedOrgId) return;
    await orgApi.updateOrganization(accessToken, selectedOrgId, payload);
    setShowEditOrg(false);
    await Promise.all([loadOrganizations(), loadOrgDetail()]);
  };

  const handleDeleteOrg = async () => {
    if (!accessToken || !selectedOrgId || !orgDetail) return;
    const confirmed = window.confirm(
      `Delete organization "${orgDetail.name}"? This removes all projects, memberships, and build data.`,
    );
    if (!confirmed) return;
    const deletedId = selectedOrgId;
    await orgApi.deleteOrganization(accessToken, deletedId);
    setShowEditOrg(false);
    setSelectedOrgId(null);
    setSelectedProjectId(null);
    setOrgDetail(null);
    await loadOrganizations();
  };

  const handleUpdateMemberRole = async (membershipId: string, memberRole: Role) => {
    if (!accessToken || !selectedOrgId) return;
    await orgApi.updateMembership(accessToken, selectedOrgId, membershipId, {
      role: memberRole,
    });
    await Promise.all([loadMembers(), refetchMembership()]);
  };

  const handleDeleteMember = async (membershipId: string) => {
    if (!accessToken || !selectedOrgId) return;
    await orgApi.deleteMembership(accessToken, selectedOrgId, membershipId);
    await Promise.all([loadMembers(), refetchMembership()]);
  };

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
            <div className="flex flex-col gap-2 sm:items-end">
              {organizations.length > 1 && (
                <label className="flex flex-col gap-1">
                  <span className="text-xs font-medium text-brand-700">
                    Switch organization
                  </span>
                  <select
                    className="input-field min-w-[12rem] sm:max-w-xs"
                    value={selectedOrgId ?? ""}
                    onChange={(e) => {
                      setSelectedOrgId(e.target.value || null);
                      setSelectedProjectId(null);
                      setShowEditOrg(false);
                    }}
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
              <div className="flex flex-wrap gap-2">
                {isAdmin && orgDetail && (
                  <button
                    type="button"
                    className="btn-secondary text-sm"
                    onClick={() => setShowEditOrg((v) => !v)}
                  >
                    {showEditOrg ? "Cancel" : "Organization settings"}
                  </button>
                )}
                <button
                  type="button"
                  className="btn-secondary text-sm"
                  onClick={() => setShowCreateOrg((v) => !v)}
                >
                  {showCreateOrg ? "Cancel" : "New organization"}
                </button>
              </div>
            </div>
          </div>

          {showCreateOrg && (
            <div className="mt-6 rounded-xl border border-violet-100 bg-brand-50/30 p-4">
              <CreateOrganizationForm
                onSubmit={handleCreateOrg}
                onCancel={() => setShowCreateOrg(false)}
                compact
              />
            </div>
          )}

          {showEditOrg && isAdmin && orgDetail && (
            <div className="mt-6 rounded-xl border border-violet-100 bg-brand-50/30 p-4">
              <h3 className="mb-4 text-sm font-semibold text-brand-900">Organization settings</h3>
              <EditOrganizationForm
                key={orgDetail.id}
                initialName={orgDetail.name}
                initialSlug={orgDetail.slug}
                onSubmit={handleUpdateOrg}
                onCancel={() => setShowEditOrg(false)}
              />
              <div className="mt-6 border-t border-violet-100 pt-4">
                <p className="text-sm text-slate-600">
                  Permanently delete this organization and all related data.
                </p>
                <button
                  type="button"
                  className="mt-3 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-100"
                  onClick={() => void handleDeleteOrg()}
                >
                  Delete organization
                </button>
              </div>
            </div>
          )}

          {loadingOrgs && (
            <p className="mt-6 text-sm text-slate-500">Loading organizations…</p>
          )}

          {!loadingOrgs && organizations.length === 0 && !showCreateOrg && (
            <div className="mt-6 rounded-xl bg-brand-50 px-4 py-8 text-center">
              <p className="text-sm text-slate-600">
                You are not a member of any organization yet.
              </p>
              <button
                type="button"
                className="btn-primary mt-4 max-w-xs"
                onClick={() => setShowCreateOrg(true)}
              >
                Create your first organization
              </button>
            </div>
          )}

          {!loadingOrgs && orgDetail && (
            <>
              {role && (
                <p className="mt-4 inline-flex rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold text-brand-800">
                  Your role: {formatRole(role)}
                  {loadingRole && " (updating…)"}
                </p>
              )}
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
            </>
          )}

          {!loadingOrgs && selectedOrgId && loadingDetail && (
            <p className="mt-6 text-sm text-slate-500">Loading organization details…</p>
          )}
        </section>

        {selectedOrgId && (
          <section className="card-surface overflow-hidden p-0">
            <div className="flex flex-col gap-3 border-b border-violet-100 bg-gradient-to-r from-brand-600 to-brand-700 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">Members</h2>
                <p className="mt-0.5 text-sm text-violet-100">
                  {memberships.length} member{memberships.length === 1 ? "" : "s"}
                </p>
              </div>
              {isAdmin && (
                <button
                  type="button"
                  className="btn-secondary border-white/30 bg-white/10 text-white hover:bg-white/20"
                  onClick={() => setShowAddMember((v) => !v)}
                >
                  {showAddMember ? "Cancel" : "Add member"}
                </button>
              )}
            </div>
            <div className="p-6">
              {showAddMember && isAdmin && (
                <div className="mb-6 rounded-xl border border-violet-100 bg-brand-50/30 p-4">
                  <AddMemberForm
                    onSubmit={handleAddMember}
                    onCancel={() => setShowAddMember(false)}
                  />
                </div>
              )}
              {loadingMembers ? (
                <p className="text-sm text-slate-500">Loading members…</p>
              ) : (
                <MembersTable
                  memberships={memberships}
                  isAdmin={isAdmin}
                  onUpdateRole={isAdmin ? handleUpdateMemberRole : undefined}
                  onDelete={isAdmin ? handleDeleteMember : undefined}
                />
              )}
            </div>
          </section>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="card-surface overflow-hidden p-0">
            <div className="flex flex-col gap-3 border-b border-violet-100 bg-gradient-to-r from-brand-600 to-brand-700 px-6 py-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-white">Projects</h2>
                <p className="mt-0.5 text-sm text-violet-100">
                  {orgDetail
                    ? `${orgDetail.projects.length} project${orgDetail.projects.length === 1 ? "" : "s"} in ${orgDetail.name}`
                    : "Build targets within the selected organization"}
                </p>
              </div>
              {isAdmin && selectedOrgId && (
                <button
                  type="button"
                  className="btn-secondary border-white/30 bg-white/10 text-white hover:bg-white/20"
                  onClick={() => setShowCreateProject((v) => !v)}
                >
                  {showCreateProject ? "Cancel" : "Add project"}
                </button>
              )}
            </div>
            <div className="p-6">
              {showCreateProject && isAdmin && (
                <div className="mb-6 rounded-xl border border-violet-100 bg-brand-50/30 p-4">
                  <CreateProjectForm
                    onSubmit={handleCreateProject}
                    onCancel={() => setShowCreateProject(false)}
                  />
                </div>
              )}
              {orgDetail && !loadingDetail ? (
                <ProjectsTable
                  projects={orgDetail.projects}
                  selectedProjectId={selectedProjectId}
                  onSelect={setSelectedProjectId}
                  isAdmin={isAdmin}
                  onDelete={isAdmin ? handleDeleteProject : undefined}
                />
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

          <ProjectDetailPanel
            project={projectDetail}
            builds={builds}
            loading={loadingProject}
            isAdmin={isAdmin}
            orgSlug={orgDetail?.slug}
            onRefresh={
              selectedProjectId
                ? () => void loadProjectData(selectedProjectId)
                : undefined
            }
          />
        </div>
      </main>
    </div>
  );
}
