// Generado por veridicus_contracts.tools.gen_ts; no editar a mano. Fuente: checks/auth_surface.py.
// Regenerar: uv run --frozen --directory contracts python -m veridicus_contracts.tools.gen_ts

export const ROLES = [
  "analista",
  "admin",
  "investigador",
] as const;

export type Role = (typeof ROLES)[number];

export const PUBLIC_OPERATIONS = [
  { method: "get", path: "/notice" },
  { method: "post", path: "/auth/login" },
] as const;

export const ENQUEUING_OPERATION_IDS = [
  "create_turn",
  "create_voice_turn",
  "launch_final_run",
  "paste_transcript",
  "retry_run",
  "set_analysis_paused",
] as const;

export const VERIDICUS_EXTENSIONS = [
  "x-veridicus-access-log",
  "x-veridicus-cookie",
  "x-veridicus-demo",
  "x-veridicus-limit",
  "x-veridicus-max-bytes",
  "x-veridicus-owner-only",
  "x-veridicus-owner-only-for-role",
  "x-veridicus-priority",
  "x-veridicus-roles",
] as const;

export const CSRF_HEADER = "X-CSRF-Token" as const;

export const CSRF_MIN_LENGTH = 32 as const;
