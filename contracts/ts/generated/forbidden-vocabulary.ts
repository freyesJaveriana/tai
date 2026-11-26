// Generado por veridicus_contracts.tools.gen_ts; no editar a mano. Fuente: integrity/forbidden-vocabulary.v2.yaml.
// Regenerar: uv run --frozen --directory contracts python -m veridicus_contracts.tools.gen_ts

export const FORBIDDEN_TERMS = [
  "mentiroso",
  "mentirosa",
  "miente",
  "mintió",
  "falso",
  "falsa",
  "verdadero",
  "verdadera",
  "engaño",
  "prueba",
  "pruebas",
  "probatorio",
  "probatoria",
  "probatorios",
  "probatorias",
  "pliego",
  "pliegos",
  "inculpa",
  "engaños",
  "falsos",
  "falsas",
  "miento",
  "mientes",
  "mienten",
  "mentimos",
  "mentís",
  "mentí",
  "mentiste",
  "mentisteis",
  "mintieron",
  "mentir",
  "mentía",
  "mentían",
  "inculpas",
  "inculpamos",
  "inculpáis",
  "inculpan",
  "inculpé",
  "inculpaste",
  "inculpasteis",
  "inculpó",
  "inculparon",
  "inculpar",
  "engañas",
  "engaña",
  "engañamos",
  "engañáis",
  "engañan",
  "engañé",
  "engañaste",
  "engañasteis",
  "engañó",
  "engañaron",
  "engañar",
] as const;

export const FORBIDDEN_SCHEMA_CATEGORIES = [
  "veracity_score",
  "is_lying",
  "truthfulness",
  "veracidad",
  "credibilidad",
] as const;

export const QUOTE_DELIMITERS = [
  "«",
  "»",
] as const;

export const FOLD_NORMALIZATION = "NFKD" as const;

export const FOLD_COMPATIBILITY_SCOPE = "word_characters" as const;

export const FOLD_ALSO_AS_SEPARATORS = "newly_dropped" as const;

export const FOLD_CASE = "casefold" as const;

export const FOLD_DROPPED_CATEGORIES = [
  "Mn",
  "Me",
  "Cf",
] as const;

export const FOLD_DROPPED_CODE_POINTS = [
  [173, 173],
  [847, 847],
  [1564, 1564],
  [4447, 4448],
  [6068, 6069],
  [6155, 6159],
  [8203, 8207],
  [8234, 8238],
  [8288, 8303],
  [12644, 12644],
  [65024, 65039],
  [65279, 65279],
  [65440, 65440],
  [65520, 65528],
  [113824, 113827],
  [119155, 119162],
  [917504, 921599],
] as const;
