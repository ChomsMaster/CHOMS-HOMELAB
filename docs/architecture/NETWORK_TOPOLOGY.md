# Topología de referencia

Fuente: inventario 23-10-2026, no consulta nueva. Tres nodos Kubernetes:
node-01 192.168.1.138, node-02 192.168.1.172 y node-03 192.168.1.134.
VIP MetalLB L2: 192.168.1.240. Traefik Gateway expone Services 80/443 y escucha
8000/8443 en Pods. Services internos 10.43.x.x y PodCIDRs observados
10.42.0.0/24, 10.42.1.0/24 y 10.42.2.0/24.

NAS 192.168.1.167: PVs NFS bajo /srv/storage/kubernetes. Colegio usa también
local-path, por lo que no toda persistencia reside en NFS. CoreDNS está presente;
split DNS se declara en Git. Router, NAT, DDNS Namecheap, WireGuard y DNS público
actuales **no verificados** por esta fuente.

Las redes Docker históricas choms-public/choms-backend/choms-database no
representan la red Kubernetes. No se borran sus archivos ni se asume su ejecución.
Véase [NetworkPolicies propuestas](../operations/NETWORK_POLICIES.md).
