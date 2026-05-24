export type WebhookProvider = "github" | "gitlab";

const WEBHOOK_BASE = import.meta.env.VITE_WEBHOOK_BASE_URL ?? "";

export function webhookUrl(provider: WebhookProvider, projectId: string): string {
  const base = WEBHOOK_BASE.replace(/\/$/, "");
  return `${base}/api/webhooks/${provider}/${projectId}/`;
}

export function webhookProviders(): WebhookProvider[] {
  return ["github", "gitlab"];
}

export function formatWebhookProvider(provider: WebhookProvider): string {
  return provider === "github" ? "GitHub" : "GitLab";
}
