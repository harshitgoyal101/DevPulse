import type { Project } from "../types/organizations";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

interface ProjectsTableProps {
  projects: Project[];
  selectedProjectId?: string | null;
  onSelect?: (projectId: string) => void;
  isAdmin?: boolean;
  onDelete?: (projectId: string) => Promise<void>;
}

export function ProjectsTable({
  projects,
  selectedProjectId,
  onSelect,
  isAdmin = false,
  onDelete,
}: ProjectsTableProps) {
  if (projects.length === 0) {
    return (
      <p className="rounded-xl bg-brand-50 px-4 py-10 text-center text-sm text-slate-600">
        No projects in this organization yet.
      </p>
    );
  }

  return (
    <div className="-mx-2 overflow-x-auto sm:mx-0">
      <table className="w-full min-w-[640px] border-separate border-spacing-0 text-sm">
        <thead>
          <tr>
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700 first:rounded-tl-lg">
              Name
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Slug
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Created
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Updated
            </th>
            {isAdmin && onDelete && (
              <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-brand-700 last:rounded-tr-lg">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {projects.map((project, index) => {
            const isSelected = selectedProjectId === project.id;
            const isLast = index === projects.length - 1;
            return (
              <tr
                key={project.id}
                className={`cursor-pointer transition ${
                  isSelected ? "bg-brand-100/70" : "hover:bg-brand-50/60"
                }`}
                onClick={() => onSelect?.(project.id)}
              >
                <td
                  className={`border-b border-violet-50 px-4 py-3.5 font-medium text-slate-800 ${
                    isLast && !isAdmin ? "rounded-bl-lg border-b-0" : ""
                  }`}
                >
                  {project.name}
                </td>
                <td className={`border-b border-violet-50 px-4 py-3.5 ${isLast ? "border-b-0" : ""}`}>
                  <code className="rounded-md bg-violet-50 px-2 py-0.5 font-mono text-xs text-brand-700">
                    {project.slug}
                  </code>
                </td>
                <td
                  className={`border-b border-violet-50 px-4 py-3.5 text-slate-600 ${
                    isLast ? "border-b-0" : ""
                  }`}
                >
                  {formatDate(project.created_at)}
                </td>
                <td
                  className={`border-b border-violet-50 px-4 py-3.5 text-slate-600 ${
                    isLast && !isAdmin ? "rounded-br-lg border-b-0" : ""
                  }`}
                >
                  {formatDate(project.updated_at)}
                </td>
                {isAdmin && onDelete && (
                  <td
                    className={`border-b border-violet-50 px-4 py-3.5 text-right ${
                      isLast ? "rounded-br-lg border-b-0" : ""
                    }`}
                    onClick={(event) => event.stopPropagation()}
                  >
                    <button
                      type="button"
                      className="text-xs font-medium text-red-600 hover:text-red-800"
                      onClick={() => void onDelete(project.id)}
                    >
                      Delete
                    </button>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
