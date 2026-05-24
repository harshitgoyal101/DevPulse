import { useState, type FormEvent } from "react";
import { authErrorMessage } from "../context/AuthContext";
import type { Role } from "../types/organizations";

interface AddMemberFormProps {
  onSubmit: (payload: { user_id: string; role: Role }) => Promise<void>;
  onCancel?: () => void;
}

export function AddMemberForm({ onSubmit, onCancel }: AddMemberFormProps) {
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState<Role>("member");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ user_id: userId.trim(), role });
      setUserId("");
      setRole("member");
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <div>
        <label htmlFor="member-user-id" className="label-text">
          User ID (UUID)
        </label>
        <input
          id="member-user-id"
          className="input-field mt-1"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
          placeholder="00000000-0000-0000-0000-000000000000"
          required
        />
      </div>
      <div>
        <label htmlFor="member-role" className="label-text">
          Role
        </label>
        <select
          id="member-role"
          className="input-field mt-1"
          value={role}
          onChange={(event) => setRole(event.target.value as Role)}
        >
          <option value="viewer">Viewer</option>
          <option value="member">Member</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="submit" className="btn-primary max-w-none px-4 py-2" disabled={submitting}>
          {submitting ? "Adding…" : "Add member"}
        </button>
        {onCancel && (
          <button type="button" className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
