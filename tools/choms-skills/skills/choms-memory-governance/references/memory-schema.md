# Esquema choms-memory-v1 y contrato MCP

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

## MCP independiente choms-memory v1

Ocho tools reales; usar tools/list como esquema ejecutable, sin inventar parámetros.
- health({}): disponibilidad, versiones, captura=false y real_memory_allowed=false.
- propose({record, request_id}): candidato inferido, sin proyección activa.
- remember({record, explicit:true, request_id}) o {scope, project_id?, id,
  expected_revision, explicit:true, request_id}: creación o aprobación CAS.
- supersede({scope, project_id?, id, expected_revision, record, explicit:true,
  request_id}): reemplazo atómico canónico; proyección pendiente se reconcilia.
- forget({scope, project_id?, id, expected_revision, explicit:true, request_id}):
  purga del linaje, wrappers oficiales + compensación validada; purge_pending ante fallo.
- review({scope, project_id?, id?, states?, limit?, budget_chars?}): lectura por ID
  o estado, sin cursor ni mutaciones de contenido. Expiración cambia estado/revisión.
- search({scope, project_id?, query, include_medium?, include_low?, limit?,
  budget_chars?}): proyección local semántica de activos; critical/high por defecto.
- checkpoint({record, explicit?, request_id}): candidate o active según consentimiento.

request_id es UUID v4; no reutilizarlo con otra petición. Recibos de mutación:
id, state, revision. Errores estructurados code/retryable; cas_conflict nunca hace
last-write-wins. Hash normalizado dedup; equivalencia semántica la revisa el agente.
Scopes son particiones de un único propietario, no ACL multiusuario.

source_kind central admite solo user_explicit/agent_inferred. Una fuente web/tool/
repository se rechaza como instrucción; la skill conserva su separación. La identidad
MCP autentica al agente; no hay verificación criptográfica de la intención humana.
Payloads reales permanecen bloqueados hasta aprobar política/operación de backups.
No marcar datos reales como fixture:. Sin backend no se finge persistencia local.

Forget-live elimina contenido canónico, huellas de recibos, vectores, grafo,
companions y caché; solo UUID/revisión/estado/IDs de peticiones opacos sobreviven.
Backup-expiry y bloques físicos tienen límites distintos: ver runbook CHOMS Memory.

## Implementación de prueba

`scripts/governance.py`: stdlib, sin red ni despacho MCP. DisabledBridge.health
expone false; cualquier otra operación central lanza BackendUnavailable.
SyntheticQueue solo opera en directorios privados `mktemp -d` con prefijo
choms-memory-test-, synthetic=True y referencias fixture:. No CLI de escritura.
JSON ≤1 MiB, ficheros 0600, directorio 0700, flock + CAS, rename atómico + fsync;
no journal ni copias de payload. No garantiza consenso distribuido entre hosts:
el backend central proporciona CAS transaccional; este fixture no lo sustituye.

Forget elimina el registro de la cola; conserva solo UUID opaco/estado en recibo.
Purga también un registro accidental inválido sin validarlo/imprimirlo. No afirma
borrado forense de RAM, SSD, snapshots o backups. Expiración se proyecta al leer:
no se recupera activo un registro vencido; expire devuelve estado expired sin
convertir una lectura en escritura. La cola nunca es una memoria oficial alternativa.
