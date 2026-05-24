import { useState, type FormEvent } from "react";
import { authErrorMessage } from "../context/AuthContext";

interface CreateOrganizationFormProps {
  onSubmit: (payload: { name: string; slug: string }) => Promise<void>;
  onCancel?: () => void;
  compact?: boolean;
}

export function CreateOrganizationForm({
  onSubmit,
  onCancel,
  compact = false,
}: CreateOrganizationFormProps) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ name: name.trim(), slug: slug.trim() });
      setName("");
      setSlug("");
    } catch (err) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={(event) => void handleSubmit(event)}
      className={compact ? "space-y-3" : "space-y-4"}
    >
      {error && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}
      <div>
        <label htmlFor="org-name" className="label-text">
          Name
        </label>
        <input
          id="org-name"
          className="input-field mt-1"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="org-slug" className="label-text">
          Slug
        </label>
        <input
          id="org-slug"
          className="input-field mt-1"
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
          pattern="[a-z0-9-]+"
          title="Lowercase letters, numbers, and hyphens only"
          required
        />
      </div>
      <div className="flex flex-wrap gap-2">
        <button type="submit" className="btn-primary max-w-none px-4 py-2" disabled={submitting}>
          {submitting ? "Creating…" : "Create organization"}
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
