// Generado por veridicus_contracts.tools.gen_ts; no editar a mano. Fuente: ui/result-labels.v2.yaml.
// Regenerar: uv run --frozen --directory contracts python -m veridicus_contracts.tools.gen_ts

export const RESULT_LABEL_KEYS = [
  "finding",
  "suggestion",
  "type_fecha",
  "type_lugar",
  "type_negacion",
  "type_numero",
  "type_otro",
  "type_persona",
  "type_secuencia",
] as const;

export type ResultLabelKey = (typeof RESULT_LABEL_KEYS)[number];

export const RESULT_LABELS = {
  "finding": "Contradicción en el relato",
  "suggestion": "Sugerencia de revisión",
  "type_fecha": "Fecha",
  "type_lugar": "Lugar",
  "type_negacion": "Negación",
  "type_numero": "Número",
  "type_otro": "Otro",
  "type_persona": "Persona",
  "type_secuencia": "Secuencia",
} as const;
