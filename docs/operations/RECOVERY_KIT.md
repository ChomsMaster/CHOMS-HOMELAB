# Exportación offline de recuperación con age

Estado: herramienta genérica preparada para pruebas sintéticas. **El kit real
sigue sin generarse**. No se ha capturado información de producción, acreditado
restauración real, RPO/RTO ni publicación. Terraform sigue siendo preparatorio.

## Contrato y autorización

La exportación recibe un único recipient público nativo age X25519, una carpeta
de selección externa y una carpeta de salida existente. No consulta hosts,
Kubernetes, Git, servicios, backups o configuración de autenticación. No usa SOPS.
Cifrar y restaurar son operaciones separadas; cifrar no requiere material de
custodia del operador. No se crean repositorios, commits, remotos ni pushes.

El operador debe autorizar por separado captura, cifrado, restauración y
publicación. Seleccionar únicamente configuración necesaria de recuperación;
no datos de aplicaciones, bibliotecas, descargas, discos o backups generales.
El programa es genérico: el nombre de un archivo no demuestra su contenido ni
consistencia. La revisión de alcance y de semántica específica es obligatoria
antes de preparar la selección. No hay bypass de seguridad en la CLI.

## Entradas exactas

Ambos directorios deben existir, ser absolutos sin componentes ambiguos,
propiedad del usuario y modo 0700. No pueden coincidir ni estar anidados.
Se rechazan symlinks en cualquier componente. Archivos: regulares, 0600,
propietario usuario y un único enlace duro. No se crean ni borran entradas.

El directorio de entrada contiene exclusivamente `selection.json` y los binarios
seleccionados. El esquema exacto del control es:

```json
{
  "version": 1,
  "entries": [
    {"file": "payload-<32 caracteres hexadecimales aleatorios>.bin",
     "size": 1,
     "sha256": "<64 caracteres hexadecimales>"}
  ]
}
```

Los marcadores son descriptivos, no fixtures ni valores ejecutables. Cada nombre
usa un identificador aleatorio opaco, sin codificar categorías ni nombres. La
selección debe estar cerrada por el operador: hash y tamaño exactos antes de
exportar. Máximo 64 entradas, 512 MiB por entrada, 1 GiB total, control de 64 KiB.
No se admiten duplicados, claves JSON repetidas, extras, vacíos o rutas relativas
a otros directorios. No se recorre un árbol ni se deduce qué archivo elegir.
Guardar la correspondencia necesaria para restaurar bajo custodia externa o como
otro payload cifrado opaco; no publicarla en el manifiesto. Las entradas en claro
ya preparadas fuera del repo siguen bajo responsabilidad del operador.

## Ejecución futura, no realizada sobre datos reales

Dependencias existentes: Bash, Python estándar moderno con soporte de dir_fd,
GNU utilidades del wrapper y age nativo instalado en el PATH estándar del sistema.
Sin descargas, plugins, SOPS ni paquetes Python adicionales. No se invocan scripts
de despliegue. El wrapper usa Python aislado y el hijo age un entorno mínimo.

```text
scripts/recovery-kit-export.sh --recipient PUBLIC_RECIPIENT --input ABS_INPUT --output ABS_OUTPUT
python3 -I -B scripts/recovery_kit.py verify --recipient PUBLIC_RECIPIENT --kit ABS_KIT
```

Los comandos son interfaces documentadas, no autorizaciones. El recipient se
valida por formato Bech32/checksum y por age durante el cifrado. Corresponde al
operador verificarlo por un canal independiente; no hay recipient predeterminado
ni valores específicos del entorno. No se imprime en mensajes del exportador.

## Salida y garantías

La carpeta publicada tiene un nombre aleatorio de 32 caracteres hexadecimales.
Contiene exclusivamente `<id-opaco>.age`, `manifest.sanitized.json` y
`checksums.sha256`. El manifiesto tiene versión, algoritmo, huella SHA-256 del
recipient y lista de ciphertexts con tamaño/hash. No contiene nombres de origen,
hashes de plaintext, servicios, hosts, namespaces, categorías ni timestamps.
Los checksums cubren todos los ciphertexts y el manifiesto; no se incluyen a sí
mismos. Son evidencia de integridad, no firma de autor ni prueba de frescura.

El plaintext se lee desde descriptores abiertos con O_NOFOLLOW, se precomprueba
por hash y se transmite directamente al stdin de age; nunca se escribe un
temporal en claro. Se comprueban hash/tamaño durante el stream, metadata antes y
después, inode de la ruta y estabilidad del directorio antes de publicar. El
operador debe congelar las entradas: no existe snapshot transaccional garantizado
frente a un proceso malicioso con el mismo UID, root o kernel comprometido.

Staging cifrado 0700 y archivos 0600; se validan estructura age X25519, tamaño,
manifiesto, checksums, permisos e inventario completo antes de renombrar el
directorio en el mismo filesystem. Se sincronizan archivos/directorios. El nombre
final aparece por un único rename; no se mezcla con un kit anterior. EXIT, INT,
TERM y HUP limpian lo no publicado y terminan el hijo age. SIGKILL/apagado puede
dejar staging **cifrado**; su revisión/eliminación requiere otra autorización.
Un error de sincronización posterior al rename puede dejar el kit publicado:
no asumir que fallo significa ausencia de salida, ni reintentar a ciegas.

El verificador sin descifrado detecta estructura inválida y cambios frente al
manifiesto/checksums. **No autentica el payload AEAD ni demuestra que pueda
restaurarse**. Solo un descifrado controlado posterior prueba integridad
criptográfica y correspondencia con datos originales. La confianza en age y
la custodia de herramientas siguen siendo requisitos del operador. No garantiza
borrado de memoria/swap ni protege un host comprometido.

No se cambia `.gitignore` del destino. Antes de publicar un kit real, alinear sus
reglas con este layout en una tarea autorizada; la política del repositorio de
custodia puede requerir revisar las excepciones de manifiestos/checksums anidados.
Nunca usar `git add -f` para eludir esa revisión.

## Pruebas y recuperación

`scripts/tests/recovery-kit-test.sh` crea exclusivamente un directorio mktemp,
fixtures artificiales y una clave efímera para descifrado sintético separado.
La clave se retira del disco antes de exportar y solo se materializa durante la
comparación sintética posterior. Las inyecciones de fallo están confinadas al
harness; no hay variables/flags que desactiven validación real.

El runbook de reconstrucción sigue siendo un procedimiento futuro. Restaurar
configuración no restaura datos de aplicaciones. Medir RPO/RTO y probar con la
custodia secundaria en un entorno aislado antes de declarar cualquier kit real
validado. Esta herramienta no sustituye una copia offsite independiente.
