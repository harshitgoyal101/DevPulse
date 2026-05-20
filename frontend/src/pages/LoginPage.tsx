import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { authErrorMessage, useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } } | null)?.from
    ?.pathname;

  const [email, setEmail] = useState("alice@acme.dev");
  const [password, setPassword] = useState("demo-password123");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (!isLoading && isAuthenticated) {
    return <Navigate to={from ?? "/"} replace />;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setSubmitting(true);
    try {
      await login({ email, password });
      navigate(from ?? "/", { replace: true });
    } catch (err) {
      setFormError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <aside className="relative hidden w-1/2 overflow-hidden bg-gradient-to-br from-brand-700 via-brand-600 to-brand-800 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-24 -right-16 h-96 w-96 rounded-full bg-brand-400/30 blur-3xl" />
        <div className="relative">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 text-lg font-bold text-white backdrop-blur">
            DP
          </div>
          <h1 className="mt-8 text-4xl font-bold tracking-tight text-white">
            DevPulse
          </h1>
          <p className="mt-4 max-w-sm text-lg text-violet-100">
            CI/CD observability for your teams. Monitor builds, projects, and
            pipelines in one place.
          </p>
        </div>
        <p className="relative text-sm text-violet-200/80">
          Self-hosted · Multi-tenant · Secure JWT auth
        </p>
      </aside>

      <main className="flex flex-1 flex-col items-center justify-center bg-gradient-to-b from-brand-50 to-white px-6 py-12">
        <div className="mb-8 text-center lg:hidden">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white shadow-glow">
            DP
          </div>
          <h1 className="mt-4 text-2xl font-bold text-brand-900">DevPulse</h1>
        </div>

        <form
          className="card-surface w-full max-w-md shadow-glow"
          onSubmit={handleSubmit}
        >
          <h2 className="text-xl font-semibold text-brand-900">Welcome back</h2>
          <p className="mt-1 text-sm text-slate-500">
            Sign in with your account email.
          </p>

          <div className="mt-6 space-y-4">
            <div>
              <label htmlFor="email" className="label-text">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className="input-field"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="label-text">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                className="input-field"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {formError && (
              <p
                className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
                role="alert"
              >
                {formError}
              </p>
            )}

            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </div>

          <p className="mt-6 rounded-xl bg-brand-50 px-3 py-2.5 text-center text-xs text-brand-800">
            Demo:{" "}
            <code className="rounded bg-white px-1.5 py-0.5 font-mono text-brand-700">
              alice@acme.dev
            </code>{" "}
            /{" "}
            <code className="rounded bg-white px-1.5 py-0.5 font-mono text-brand-700">
              demo-password123
            </code>
          </p>
        </form>
      </main>
    </div>
  );
}
