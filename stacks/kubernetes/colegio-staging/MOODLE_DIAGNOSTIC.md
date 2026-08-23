# Moodle Checkpoint 2 — diagnóstico aislado

Fecha de evidencia: 2026-08-23. El laboratorio fue temporal, interno y sin
DNS público, Certificate, Authelia, HTTPRoute, web institucional, Gibbon ni
acceso a producción. Usó los mismos digests de Moodle 5.2.2 y MariaDB 11.4,
PVC temporales, Secrets efímeros y `DocumentRoot /var/www/html/public`.

## Resultado reproducido

- Instalación CLI oficial: pasó.
- Login administrativo ficticio: pasó.
- Creación de curso ficticio: pasó.
- Actividad `assign`: falló de forma reproducible.

La excepción fue `dml_write_exception` / `dmlwriteexception` al insertar en
`mdl_assign`. Moodle reportó `Column 'markingworkflow' cannot be null`.
La traza pasó por `assign_add_instance`, `add_instance` y `add_moduleinfo`.
La transacción delegada quedó abierta al salir por la excepción, que es una
consecuencia del fallo de la llamada y no corrupción de la base.

## Evidencia técnica sanitizada

- MariaDB: 11.4.12; `utf8mb4`, `utf8mb4_unicode_ci`,
  `STRICT_TRANS_TABLES`, `innodb_strict_mode=ON`, `REPEATABLE-READ`.
- Esquema Moodle: versión 2026042002; módulo assign: 2026042000.
- Tablas requeridas presentes y InnoDB: `mdl_assign`,
  `mdl_assign_submission`, `mdl_course_modules`, `mdl_context`, `mdl_modules`.
- Usuario Moodle tenía `ALL PRIVILEGES` sobre el esquema aislado.
- `moodledata` era escribible (`0777` en el PVC temporal); no fue la causa.
- El warning de `io_uring` de MariaDB fue un fallback normal a `libaio` y no
  participó en el error.

## Causa y corrección mínima propuesta

La API oficial `add_moduleinfo()` recibió un objeto incompleto para Moodle
5.2. La imagen y el esquema son compatibles; la llamada debe incluir los
defaults del formulario oficial, como mínimo:

```php
'markingworkflow' => 0,
'markingallocation' => 0,
'gradepenalty' => 0,
'markercount' => 1,
```

La corrección propuesta solo modifica el objeto de entrada de la API en el
laboratorio del Checkpoint 2. No cambia MariaDB, permisos, esquema, imagen,
configuración de producción ni datos reales. Debe repetirse en un laboratorio
nuevo con instalación, actividad, cron, reinicio, persistencia, backup y
restore antes de desplegar Moodle.

No se declara Moodle operativo ni se versionan Secrets, contraseñas, dumps,
PVC, logs completos o certificados privados.
