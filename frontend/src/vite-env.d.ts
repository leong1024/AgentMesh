/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** If set (e.g. http://127.0.0.1:8080), analyze stream bypasses Vite proxy for incremental SSE. */
  readonly VITE_ORCHESTRATOR_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
