import { formatRole } from "../lib/roles";
import type { Membership, Role } from "../types/organizations";

interface MembersTableProps {
  memberships: Membership[];
  isAdmin: boolean;
  onUpdateRole?: (membershipId: string, role: Role) => Promise<void>;
  onDelete?: (membershipId: string) => Promise<void>;
}

export function MembersTable({
  memberships,
  isAdmin,
  onUpdateRole,
  onDelete,
}: MembersTableProps) {
  if (memberships.length === 0) {
    return (
      <p className="rounded-xl bg-brand-50 px-4 py-10 text-center text-sm text-slate-600">
        No members in this organization yet.
      </p>
    );
  }

  return (
    <div className="-mx-2 overflow-x-auto sm:mx-0">
      <table className="w-full min-w-[480px] border-separate border-spacing-0 text-sm">
        <thead>
          <tr>
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700 first:rounded-tl-lg">
              Email
            </th>
            <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-brand-700">
              Role
            </th>
            {isAdmin && (
              <th className="border-b border-violet-100 bg-brand-50/80 px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-brand-700 last:rounded-tr-lg">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {memberships.map((membership, index) => (
            <tr key={membership.id} className="transition hover:bg-brand-50/60">
              <td
                className={`border-b border-violet-50 px-4 py-3.5 font-medium text-slate-800 ${
                  index === memberships.length - 1 && !isAdmin ? "rounded-bl-lg border-b-0" : ""
                }`}
              >
                {membership.email}
              </td>
              <td
                className={`border-b border-violet-50 px-4 py-3.5 ${
                  index === memberships.length - 1 && !isAdmin ? "border-b-0" : ""
                }`}
              >
                {isAdmin && onUpdateRole ? (
                  <select
                    className="input-field py-1.5 text-sm"
                    value={membership.role}
                    onChange={(event) =>
                      void onUpdateRole(membership.id, event.target.value as Role)
                    }
                  >
                    <option value="viewer">Viewer</option>
                    <option value="member">Member</option>
                    <option value="admin">Admin</option>
                  </select>
                ) : (
                  <span className="inline-flex rounded-full bg-brand-100 px-2.5 py-0.5 text-xs font-semibold text-brand-800">
                    {formatRole(membership.role)}
                  </span>
                )}
              </td>
              {isAdmin && (
                <td
                  className={`border-b border-violet-50 px-4 py-3.5 text-right ${
                    index === memberships.length - 1 ? "rounded-br-lg border-b-0" : ""
                  }`}
                >
                  {onDelete && (
                    <button
                      type="button"
                      className="text-xs font-medium text-red-600 hover:text-red-800"
                      onClick={() => void onDelete(membership.id)}
                    >
                      Remove
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
