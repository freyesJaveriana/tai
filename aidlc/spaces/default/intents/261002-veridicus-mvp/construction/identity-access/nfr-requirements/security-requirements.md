# Requisitos de seguridad — U3 identity-access

**Insumos.** Flujos F1–F9 de `functional-design/functional-spec.md` (functional-spec) y reglas
BR1.1–BR7.3 de `functional-design/rules.md` (rules) de esta unidad; FR1, FR9, NFR10 y NFR11 de
`inception/requirements-analysis/requirements.md` (requirements); C1 y C12 de
`inception/contract-design/contract-summary.md` (contract-summary); respuestas P1–P4 de
`nfr-requirements-questions.md`; prácticas de `team.md` y `project.md`.

Cada requisito hereda el ID del NFR de Inception que detalla. Niveles de prueba de team-practices:
nivel 0 (unitarias, cada PR), nivel 1 (integración con PostgreSQL y Redis reales, cada PR), nivel 3
(E2E). Los comandos están en `tech-stack-decisions.md` §4.

## 1. Frontera de la unidad (AUTONOMIA-04)

| Componente | Dónde corre | Qué datos cruzan su frontera |
|---|---|---|
| IdentityAccess y autorización de ConsoleApi | `session-api`, dentro del clúster | Cookie, token anti-CSRF y respuestas al navegador, dentro del clúster |
| Contador de intentos | Redis, dentro del clúster | Solo claves derivadas (HMAC) y contadores |
| `Job` `create-admin` | Dentro del clúster | Lee usuario y contraseña de un Secret; no los imprime |

U3 no hace ninguna llamada fuera del clúster. Datos que guarda: nombres de usuario y hashes de
contraseña (dato **confidencial**), tokens de sesión solo como hash (**restringido**).

## 2. Modelo de amenazas (STRIDE)

| # | Amenaza | STRIDE | Riesgo | Mitigación |
|---|---|---|---|---|
| T1 | Probar contraseñas desde la consola | Spoofing | Alto | NFR10.5 |
| T2 | Robo de la base y ataque fuera de línea a los hashes | Information disclosure | Medio | NFR10.1, NFR10.2 |
| T3 | Robo o reutilización de la cookie de sesión | Spoofing | Medio | NFR10.3 |
| T4 | Petición falsificada desde otro sitio (CSRF) | Tampering | Medio | NFR10.4 |
| T5 | Enumerar usuarios por la respuesta o por el tiempo | Information disclosure | Medio | NFR10.6, NFR10.5 |
| T6 | Una ruta nueva sin control de rol | Elevation of privilege | Alto | NFR10.9 |
| T7 | Un usuario desactivado sigue operando | Elevation of privilege | Medio | NFR10.3 |
| T8 | Contraseña o token en logs o columnas | Information disclosure | Alto | NFR10.7 |
| T9 | Reescribir el historial de usuarios | Repudiation | Medio | NFR11.1 |
| T10 | Muchos inicios de sesión a la vez agotan la memoria (Argon2id usa 64 MiB) | Denial of service | Medio | NFR8.1 |

## 3. Requisitos

### NFR10 — Seguridad de la aplicación

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR10.1 | Las contraseñas se guardan con Argon2id (P1 = A). | Parámetros `m = 65 536 KiB`, `t = 3`, `p = 1`, sal aleatoria de 16 bytes y hash de 32 bytes; el hash guardado empieza por `$argon2id$v=19$m=65536,t=3,p=1$`. Si los parámetros configurados cambian, el siguiente inicio de sesión correcto vuelve a calcular el hash. | Nivel 0 (prefijo y re-hash) y nivel 1 (E2) |
| NFR10.2 | Política de contraseñas (P2: 8 con composición y lista común). | Se rechazan con `422` `user.weak_password` las contraseñas de menos de 8 o más de 128 caracteres, sin al menos una mayúscula, una minúscula, un número y un símbolo, o presentes (sin distinguir mayúsculas) en la lista de contraseñas comunes guardada en `services/session-api/` con su SHA-256. Aplica en `POST /users` y en `create-admin` (que termina con código distinto de 0). Una prueba por cada condición y su control positivo. | Nivel 0 |
| NFR10.3 | La sesión web caduca por inactividad y por tiempo total (P3 = A). | Token de 256 bits aleatorios; en la base solo su SHA-256. Caduca a los 1 800 s sin peticiones autenticadas y a los 43 200 s del inicio de sesión. La cookie lleva `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/` y `Max-Age=43200`. Desactivar al usuario o cerrar sesión hace que la petición siguiente responda `401` (sin caché de sesiones). Pruebas con reloj controlado: 1 799 s válida, 1 801 s vencida; 43 199 s válida con actividad, 43 201 s vencida. | Nivel 0 y nivel 1 |
| NFR10.4 | El token anti-CSRF no se puede adivinar ni comparar por tiempo. | 256 bits aleatorios por sesión web; comparación en tiempo constante (`hmac.compare_digest`); sin él o distinto, `403` `auth.csrf` sin filas (BR1.5, E4). | Nivel 0 y nivel 1 |
| NFR10.5 | Se limitan los intentos fallidos (P4 = A). | Por usuario normalizado y por dirección de origen: al quinto fallo dentro de 15 minutos, las peticiones siguientes de ese usuario o de ese origen reciben `429` `auth.too_many_attempts` con `Retry-After: 900` durante 15 minutos, exista o no el usuario, sin verificar la contraseña. Un inicio de sesión correcto pone a cero el contador del usuario. La clave en Redis es un HMAC-SHA256 del usuario (nunca el usuario en claro) y caduca sola. La dirección de origen sale de `X-Forwarded-For` solo cuando la petición viene del proxy de confianza configurado. Pruebas: 4 fallos y luego éxito; 5 fallos y luego `429` con contraseña correcta; mismo resultado con usuario inexistente. | Nivel 1 |
| NFR10.6 | No se revela si un usuario existe. | Usuario inexistente, contraseña errónea y usuario desactivado devuelven el mismo estado y el mismo cuerpo byte a byte (BR1.2, E1), y los tres caminos ejecutan exactamente una verificación Argon2id (el inexistente contra el hash señuelo). | Nivel 0 (espía sobre el verificador) y nivel 1 |
| NFR10.7 | Ninguna contraseña ni token aparece en columnas ni logs. | Tras crear un usuario con una contraseña sembrada e iniciar sesión, 0 coincidencias de la contraseña, del token de sesión y del token anti-CSRF en todas las columnas de texto y en la salida de logs capturada (E2); los logs llevan `user_id`, nunca el nombre de usuario. | Nivel 1 |
| NFR10.8 | El primer `admin` nace sin exponer su contraseña. | `create-admin` lee usuario y contraseña de variables que vienen de un Secret, valida NFR10.2, no los imprime y termina con código distinto de 0 si ya existe un `admin` activo (BR3.1, E10). Su `Job` corre sin root, con `backoffLimit: 0` y `ttlSecondsAfterFinished`. | Nivel 1 y política de manifiestos de U2 |
| NFR10.9 | La autorización niega por defecto. | Una ruta que no es pública y no declara `x-veridicus-roles` se rechaza con `403` aunque el contrato la permitiera; cada celda «No» y «Solo propias» de FR1.2 tiene su prueba `403` con Problem Details en español (BR4.1–BR4.3, E3, E5). | Nivel 1 |
| NFR10.10 | Las respuestas de autenticación no se guardan en caché. | `POST /auth/login`, `POST /auth/logout` y `GET /auth/me` responden `Cache-Control: no-store`. | Nivel 0 |

### NFR11 — Integridad y auditoría

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR11.1 | El historial de usuarios solo admite inserciones y entra en la prueba común. | `UserChange` con actor y hora no nulos (salvo `actor_kind: system` en el alta del primer `admin`); `UPDATE` y `DELETE` fallan por permisos con el usuario de la aplicación; la tabla está registrada en `AuditConvention` (BR6.1–BR6.3, E13, E14). | Nivel 1 |
| NFR11.2 | Ningún camino de la consola escribe el umbral. | Regla estática con control negativo: solo el cargador de configuración asigna el ajuste del umbral (BR5.2, E12); la prueba de OpenAPI es la de U1 (E11). | Nivel 0 |

### NFR1 — Soberanía de datos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR1.1 | U3 no hace llamadas fuera del clúster. | El código de U3 no abre conexiones salvo a PostgreSQL y Redis configurados; la `NetworkPolicy` de U2 niega la salida a internet de `session-api`. | Política estática de U2 (nivel 0) |

### NFR12 — Datos sintéticos

| ID | Requisito | Criterio medible | Verificación |
|---|---|---|---|
| NFR12.1 | Usuarios de prueba ficticios. | Todo usuario de las pruebas y de los datos de demostración tiene nombre del catálogo sintético de U1. | Revisión del PR y comprobación de U1 |

## 4. Correspondencia con AUTONOMIA-01..05

| Regla | Qué aporta U3 | Requisitos |
|---|---|---|
| AUTONOMIA-01 | El primer `admin` y el umbral solo cambian por artefactos revisados (`Job` y PR) | NFR10.8, NFR11.2 |
| AUTONOMIA-02 | Cada requisito tiene su prueba y su umbral | Todas |
| AUTONOMIA-03 | Toda acción queda con quién y cuándo; nadie reescribe el historial | NFR11.1 |
| AUTONOMIA-04 | Sin llamadas externas | NFR1.1 |

## 5. Precisiones a artefactos ya aprobados

No edité ningún artefacto aprobado; decides en la aprobación si se actualizan.

| Artefacto | Qué precisa | Origen |
|---|---|---|
| `contract-design/contract-summary.md` (C1 `ErrorCode` y `/auth/login`) | Añade `auth.too_many_attempts` (`429` con `Retry-After`) en `POST /auth/login`, y `user.weak_password` (`422`) en `POST /users`. | P2, P4 |
| `contract-design/contract-summary.md` (C1 `ErrorCode`) | Añade un `code` genérico `system.unavailable` (`503`) para cuando la base o Redis no responden durante el inicio de sesión; `functional-spec.md` §9 pide un error del sistema que hoy no tiene `code`. | NFR8.2 |
| `contract-design/contract-summary.md` (C15) | Añade las métricas de autenticación de `observability-requirements.md` (por un PR de U1, dueño U3). | NFR15.1 |
