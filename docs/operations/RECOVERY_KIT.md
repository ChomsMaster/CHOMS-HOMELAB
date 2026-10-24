# Kit privado de recuperación de configuración

**Preparación de código: exportador NO ejecutado, sin acceso a producción ni
lectura de secretos.** No se ha creado ni inspeccionado el repositorio privado.
El exportador funciona offline sobre archivos que un operador haya preparado
previamente, en otra tarea autorizada. No ejecuta SSH, kubectl, backups ni SOPS
decrypt; tampoco instala herramientas, crea claves, hace commit o push.

Destino fijo: `../choms-recovery-private`, repositorio Git local independiente.
El operador confirma su visibilidad privada; no puede verificarse offline. La
clave age se custodia fuera de ambos repositorios y del directorio de entrada.
No basta con guardar la única clave junto al kit: conservar una segunda copia
offline y probar su disponibilidad en una recuperación aislada.

## Contrato exacto de entradas

Directorio externo propiedad del operador con modo 0700; archivos regulares
no vacíos, no symlinks, propietario operador y modo 0600. No se recorre ni se
archiva ningún árbol de aplicación. Solo se cifran estos nombres:

| Archivo de entrada | Contenido que prepara el operador |
|---|---|
| kubernetes-secrets.json | List/SecretList de objetos Secret; no kubeconfig ni todos los recursos del clúster |
| k3s-token | Token original del servidor, necesario para recuperar bootstrap/datastore |
| k3s-snapshot | Copia consistente del datastore: SQLite o snapshot etcd según contrato |
| k3s-snapshot-meta.json | Tipo, consistencia, versión real y uso de secrets-encryption |
| authelia-configuration.yml | Configuración efectiva de Authelia, no solo plantilla pública |
| restic-password | Contraseña real del repositorio Restic existente, sin mostrarla |
| ansible-vars.yml | Variables privadas necesarias para reconstrucción; sin volcados de aplicaciones |
| network-dns.md | Router/NAT, LAN, NAS/NFS, DNS/split DNS, VPN, orden y responsables de restauración |
| authelia-users.yml (opcional) | Base de identidades de archivo si el backend de autenticación la usa |
| k3s-encryption-config.json (condicional) | Configuración/llaves originales si secrets-encryption está habilitado |

La captura de Secrets requiere una operación explícita y separada de lectura
autorizada. Excluir credenciales efímeras si su renovación resulta preferible;
restaurar Helm release Secrets o tokens de nodo a ciegas causa ownership obsoleto.
No imprimir el JSON ni conservarlo en este repositorio. El exportador no limpia
metadata: el saneado para restaurar se hace en memoria y por objeto revisado.

**Baseline documentado: un servidor K3s con SQLite**, no etcd. Una copia caliente
del archivo state.db no es un snapshot consistente. Preparar una copia mediante
la API SQLite backup o con el servicio detenido según procedimiento autorizado.
Para otro datastore, no reutilizar instrucciones SQLite. La metadata exigida es:

```json
{
  "datastore": "sqlite",
  "consistency": "sqlite-backup-api",
  "k3s_version": "VERSION_REAL_DEL_SNAPSHOT",
  "secrets_encryption": false
}
```

El booleano y la versión son datos que el operador debe verificar, no defaults
que certifiquen el estado real. El script admite offline/SQLite backup y snapshot
etcd explícitos; comprueba cabecera SQLite y límites de tamaño. No certifica la
consistencia del snapshot ni el conjunto de archivos de bootstrap de otra versión.
Si hay secrets-encryption exige su configuración cifrada adicional. Versiones,
flags y rutas de recuperación deben coincidir con el host original.

## Preparación y ejecución FUTURA del operador

Requiere GNU coreutils, Python 3, Git, SOPS 3.9 o posterior y age 1.2 o posterior.
Instalar SOPS y age por el procedimiento de dependencias aprobado, sin incluir
credenciales ni herramientas privadas en CI. La única ejecución de este bloque
es validación estática: nunca se llama al exportador.

1. Crear/custodiar la identidad age fuera de los repositorios. No compartirla,
   imprimirla ni escribirla en esta documentación. El script exige una identidad
   age nativa, archivo propiedad del operador con modo 0600, y deriva su recipient
   público en memoria mediante age-keygen; rechaza ejecución sin ella.
2. Preparar el repositorio independiente y comprobar privadamente su visibilidad
   en el proveedor. En una tarea autorizada, confirmar la decisión local:

```bash
git -C ../choms-recovery-private config --local choms.recoveryPrivateApproved true
# La variable indica una ruta, no el contenido de la clave.
export SOPS_AGE_KEY_FILE=/RUTA_EXTERNA/identidad-age
./scripts/recovery-kit-export.sh /RUTA_EXTERNA/entradas-recovery
```

3. El repo privado debe tener como tracked solo `.gitignore` y ciphertext bajo
   kits/; un README u otro archivo tracked ajeno al contrato exige revisar el
   destino antes de exportar. No se inicializa automáticamente un repo nuevo.
4. El script publica un directorio único y completo solo cuando todo se ha
   cifrado. Los bytes en claro pasan exclusivamente por un pipe hacia SOPS;
   no crea temporales en claro. SOPS cifra todo el archivo, también claves de
   configuración/comentarios. Los errores se reducen a mensajes fijos sin valores.
   .pending se elimina en fallo; los inputs externos y su borrado seguro siguen
   siendo responsabilidad del operador. No copiar estos inputs al repo público.
5. Revisar estructura y recipient sin descifrar contenido en logs. Hacer commit
   y push únicamente de ciphertext y .gitignore tras decisión del propietario.
   Gitignore ayuda a prevenir errores, pero no impide git add -f ni elimina
   secretos que ya estuvieran en historial. No confiar solo en visibilidad privada.

## Alcance y prueba de recuperación

No incluye datos de Jellyfin, Nextcloud, bibliotecas, descargas, bases de datos
de aplicaciones, caches, PVCs ni imágenes de disco. No exporta tfstate ni
kubeconfig. Es un kit de credenciales/configuración y datastore K3s, **no** una
copia de datos de aplicaciones. Límites: datastore 512 MiB, Secrets 32 MiB,
cada configuración 4 MiB. Si se supera un límite, revisar alcance; no sustituir
el snapshot por un backup de datos ni ampliar límites sin evaluar el contenido.

El directorio puede contener otros archivos: no se incluyen. Cada entrada de la
allowlist debe ser revisada por el operador para evitar datos de aplicación con
un nombre de configuración; ninguna herramienta puede demostrar intención a
partir del nombre. El datastore puede contener metadatos/Secrets de Kubernetes;
ese contenido es parte expresa del kit cifrado.

Probar con la copia secundaria de la clave, en un equipo aislado con tmpfs
privado y sin logging de comandos. Descifrar una entrada a un pipe o fichero
0600 en ese tmpfs, validar su estructura sin imprimir valores, recuperar K3s
con el token original y verificar identidades/servicios en laboratorio. No usar
`sops decrypt` sin redirección: escribiría el contenido en el terminal. No
descifrar en el working tree. Seguir [REBUILD_RUNBOOK.md](REBUILD_RUNBOOK.md),
registrando solo fecha, versión y resultado agregado. Esta prueba está pendiente.
