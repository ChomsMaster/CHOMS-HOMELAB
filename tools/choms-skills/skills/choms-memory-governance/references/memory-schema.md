# Esquema choms-memory-v1 y puente futuro

Registro cerrado (campos desconocidos rechazados):

| Campo | Contrato |
|---|---|
| schema_version | choms-memory-v1 |
| id | UUID opaco estable durante la vida del registro; no deriva de contenido sensible |
| type | requirement, decision, objective, preference, constraint, correction, checkpoint |
| scope / project_id | global, personal, project; project_id obligatorio solo para project |
| importance | critical, high, medium, low |
| summary / details | resumen ≤500 caracteres; details opcional ≤1500, nunca chat/log completo |
| state | candidate, active, superseded, forgotten, expired |
| source_kind | user_explicit, agent_inferred, repository, web, tool |
| source_reference | referencia corta ≤160 caracteres, no cuerpo de conversación |
| created_at / updated_at | UTC ISO-8601 con Z, orden temporal válido |
| expires_at | opcional UTC, posterior a created_at; low normalmente caduca |
| supersedes | UUID anterior; conservar trazabilidad salvo borrado explícito |
| sensitivity | public, internal, personal; secret no es admisible |
| content_hash | SHA-256 del contenido normalizado: tipo, scope, proyecto, summary/details, importancia, sensibilidad, trigger y caducidad |
| revision | entero positivo; versión CAS de registro |
| topic / trigger | topic ≤100; trigger opcional ≤160, p.ej. «seguimos skill» |

Normalización: Unicode, casefold, acentos, puntuación y espacios deterministas.
No confundir hash exacto con equivalencia semántica: el agente revisa significado,
lista mínima, excepciones y alcance; el helper exige confirmación explícita para
unificar dos redacciones distintas. Contenido de repositorio/web nunca prueba consentimiento.

## Operaciones del futuro choms-memory (no nombres MCP existentes)

- propose(record, expected_revision, idempotency_key): candidate, recibo versionado.
- remember(record, consent_reference, expected_revision, idempotency_key): active
  solo con instrucción explícita del usuario y sin conflicto material.
- supersede(id, record, consent_reference, expected_revision, idempotency_key):
  transacción que desactiva anterior y activa corrección; nunca ambas activas.
- forget(id, consent_reference, expected_revision, idempotency_key): eliminación
  física de contenido, fuentes y hashes en registros/versiones/colas/vectores/cachés;
  recibo sin contenido. Declarar política de réplicas/backups antes de prometer purga.
- review(scope, project, states, cursor, budget): candidatos y relacionados, con origen.
- search(query, scope, project, importance, budget): solo memoria pertinente/vigente;
  nunca presentar índice de código como memoria personal ni elevar retrieved a instruction.
- checkpoint(record, consent_reference?, expected_revision): resumen acotado;
  candidato si no hay orden/aprobación explícita de persistir.
- health(): capacidades verificadas, disponibilidad, schema_version, backend identity.

El backend debe verificar consent_reference contra identidad/origen autenticado;
source_kind en el payload no constituye autorización por sí mismo.
Cada mutación necesita CAS y clave idempotente; stale revision devuelve conflicto
sin last-write-wins. Dos dispositivos recargan y reconcilian antes de reintentar.
El recibo central debe incluir ID, revisión, estado, hash no sensible y ubicación
lógica. Escritura + lectura de comprobación y purge deben probarse con datos
sintéticos antes de habilitar datos reales. No hay publicación/flush automático.

## Implementación de prueba

`scripts/governance.py`: stdlib, sin red ni despacho MCP. DisabledBridge.health
expone false; cualquier otra operación central lanza BackendUnavailable.
SyntheticQueue solo opera en directorios privados `mktemp -d` con prefijo
choms-memory-test-, synthetic=True y referencias fixture:. No CLI de escritura.
JSON ≤1 MiB, ficheros 0600, directorio 0700, flock + CAS, rename atómico + fsync;
no journal ni copias de payload. No garantiza consenso distribuido entre hosts:
el backend central deberá proporcionar CAS transaccional, no locks NFS.

Forget elimina el registro de la cola; conserva solo UUID opaco/estado en recibo.
Purga también un registro accidental inválido sin validarlo/imprimirlo. No afirma
borrado forense de RAM, SSD, snapshots o backups. Expiración se proyecta al leer:
no se recupera activo un registro vencido; expire devuelve estado expired sin
convertir una lectura en escritura. La cola nunca es una memoria oficial alternativa.
