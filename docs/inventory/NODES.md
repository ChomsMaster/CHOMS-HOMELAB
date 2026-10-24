# Inventario de nodos

Referencia: [inventario de 23-10-2026](BASELINE_2026-10-23.md), sin nueva consulta.

| Nodo | IP privada | Rol | SO/recursos |
|---|---|---|---|
| choms-node-01 | 192.168.1.138 | K3s control-plane | Debian 13; 4 CPU; 5914800 KiB |
| choms-node-02 | 192.168.1.172 | worker según Ansible | Debian 13; 4 CPU; 24501612 KiB |
| choms-node-03 | 192.168.1.134 | worker según Ansible | Debian 13; 4 CPU; 7960880 KiB |
| choms-nas | 192.168.1.167 | servidor NFS declarado/observado en PVs | SO/recursos no verificados |

Roles worker no aparecían etiquetados en kubectl get nodes. La capacidad indicada
no acredita capacidad libre ni hardware físico. RP3 y equipo de desarrollo no
fueron comprobados por el inventario como nodos de producción Kubernetes.
