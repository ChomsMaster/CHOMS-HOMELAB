# OpenHands — gate de aislamiento bloqueado; no desplegado

Fuente oficial fijada: OpenHands v1.33.0, `helm/agent-canvas`, chart 0.1.0,
Kubernetes >=1.24. El README del tag declara una instancia compartida: agentes
en un mismo Pod/PVC. Los sandboxes aislados por ejecución se atribuyen a OHE.

El requisito CHOMS exige sandbox por conversación. No equivale a usar un
namespace, una ServiceAccount propia o NetworkPolicy sobre ese Pod compartido.
Por eso no se crea namespace, release, RBAC, Secret, workspace ni ruta de red.
No se entrega un values que parezca resolver un aislamiento inexistente.

Gates para reanudar:

1. Obtener un artefacto oficial/self-host con contrato comprobable de sandbox
   por conversación, o aprobar explícitamente un controlador de sandboxes distinto.
2. Renderizar el chart fijado y verificar ausencia de privileged, hostPath,
   host namespaces y socket Docker; nunca usar default SA, admin/cluster-admin,
   kubeconfig ni secretos de host/GitHub/age dentro del sandbox.
3. Demostrar que el agente no hereda la identidad Kubernetes del controlador.
   RBAC mínimo de controlador exclusivamente en su namespace de sandboxes;
   ningún token de ServiceAccount montado en los sandboxes.
4. Conversaciones separadas de workspaces; clone desechable solo del repo público.
5. Código nativo Codebase Memory mediante la integración oficial `.openhands/mcp.json`,
   con cache/allowed-root propios de cada workspace, sin hooks ni índices compartidos.
6. Cognee por ClusterIP autenticado; permiso de OmniRoute a 20129 limitado a
   namespaceSelector y podSelector. No ampliar CIDR del API ni publicar /v1.
7. Probar dos conversaciones, aislamiento de host/clúster, persistencia y restore
   sintético antes de habilitar el componente.

`OPENHANDS_DEPLOYMENT=BLOCKED_ISOLATION_CONTRACT`.
`OPENHANDS_INFERENCE=BLOCKED_EXPECTED`: no se configuran proveedores ni modelos.
La imagen candidata tiene digest registrado en el lock; no se desplegó ni se
ha declarado aceptada por el hecho de resolver su digest.
