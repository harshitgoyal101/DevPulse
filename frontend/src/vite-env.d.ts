/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_WEBHOOK_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
