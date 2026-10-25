# OmniRoute — bloqueos de publicación resueltos

Fecha: 2026-10-25. Dataset autorizado: `choms-homelab-public`.
Commit de publicación: `c1af248f1f060393d5543f1a5e4c5f7ee41ffa3f`.

## Evidencia y resolución

1. El self-check HTTP-01 de cert-manager recibía SERVFAIL mediante CoreDNS.
   Se declaró `--acme-http01-solver-nameservers=1.1.1.1:53,1.0.0.1:53`
   conservando el chart v1.21.1. No se modificó CoreDNS. La emisión terminó
   correctamente y preservó los SAN previos.
2. La API escuchaba en todas las interfaces y Service/EndpointSlice eran correctos,
   pero el origen Flannel seleccionado por el control plane no coincidía con
   la excepción de NetworkPolicy. Se corrigió `10.42.0.1/32` a `10.42.0.0/32`.
   Después, PodIP y ClusterIP devolvieron 401 sin clave; el túnel loopback también.
3. La API pública `/v1/models` devolvió 404 y no tiene ruta backend publicada.
   Dashboard/administración usan 20128 con Authelia. API privada: ClusterIP 20129.

## Fuentes verificables

- [Runbook](../operations/OMNIROUTE.md).
- [Values cert-manager](../../stacks/kubernetes/cert-manager/values.yaml).
- [NetworkPolicies](../../stacks/kubernetes/omniroute/networkpolicies.yaml).
- [HTTPRoutes](../../stacks/kubernetes/omniroute/routes.yaml).
- [Services y Deployments](../../stacks/kubernetes/omniroute/workloads.yaml).
- [Worklog](../context/WORKLOG.md).

No contiene transcripciones, credenciales, tokens de challenge ni datos privados.
Los códigos 401/404 son evidencias de los recorridos probados, no una prueba
completa de aislamiento ni de funcionamiento de proveedores.
