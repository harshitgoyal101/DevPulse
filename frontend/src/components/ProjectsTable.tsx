import type { Project } from "../types/organizations";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

interface ProjectsTableProps {
  projects: Project[];
}

export function ProjectsTable({ projects }: ProjectsTableProps) {
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
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700 first:rounded-tl-lg last:rounded-tr-lg">
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
          </tr>
        </thead>
        <tbody>
          {projects.map((project, index) => (
            <tr
              key={project.id}
              className="transition hover:bg-brand-50/60"
            >
              <td
                className={`border-b border-violet-50 px-4 py-3.5 font-medium text-slate-800 ${
                  index === projects.length - 1 ? "rounded-bl-lg border-b-0" : ""
                }`}
              >
                {project.name}
              </td>
              <td
                className={`border-b border-violet-50 px-4 py-3.5 ${
                  index === projects.length - 1 ? "border-b-0" : ""
                }`}
              >
                <code className="rounded-md bg-violet-50 px-2 py-0.5 font-mono text-xs text-brand-700">
                  {project.slug}
                </code>
              </td>
              <td
                className={`border-b border-violet-50 px-4 py-3.5 text-slate-600 ${
                  index === projects.length - 1 ? "border-b-0" : ""
                }`}
              >
                {formatDate(project.created_at)}
              </td>
              <td
                className={`border-b border-violet-50 px-4 py-3.5 text-slate-600 ${
                  index === projects.length - 1 ? "rounded-br-lg border-b-0" : ""
                }`}
              >
                {formatDate(project.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
