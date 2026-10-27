"""Render only the CHOMS Memory workload; no network/runtime operations."""
from pathlib import Path
import hashlib
import json
import yaml

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'stacks/kubernetes/choms-memory'
# CRI LocalResolve accepts content-addressed image IDs without a repository alias.
IMAGE='sha256:8ceaeca731beb3c888384e3837c9232de05c1090e935dbb1997f76049e037d4d'


def render():
    sources={name:(ROOT/'tools/choms-memory'/name).read_text() for name in
             ('server.py','backend.py','contract.py','purge.py','purge-contract.json','stdio_bridge.py','network_guard.py','admin.py')}
    sources['001.sql']=(ROOT/'tools/choms-memory/migrations/001.sql').read_text()
    sources['governance.py']=(ROOT/'tools/choms-skills/skills/choms-memory-governance/scripts/governance.py').read_text()
    digest=hashlib.sha256(json.dumps(sources,sort_keys=True).encode()).hexdigest()
    code='choms-memory-code-'+digest[:12]
    labels={'app.kubernetes.io/name':'choms-memory','app.kubernetes.io/part-of':'choms-memory'}
    def meta(name):return {'name':name,'namespace':'choms-memory','labels':labels}
    config={'apiVersion':'v1','kind':'ConfigMap','metadata':meta(code),'immutable':True,'data':sources}
    env={'DB_PROVIDER':'postgres','DB_HOST':'postgresql.choms-memory.svc.cluster.local','DB_PORT':'5432',
         'DB_NAME':'cognee','DB_USERNAME':'choms_memory_adapter','VECTOR_DB_PROVIDER':'pgvector',
         'VECTOR_DATASET_DATABASE_HANDLER':'pgvector_shared','ENABLE_BACKEND_ACCESS_CONTROL':'true',
         'GRAPH_DATABASE_PROVIDER':'kuzu','SYSTEM_ROOT_DIRECTORY':'/state/system','DATA_ROOT_DIRECTORY':'/state/data',
         'MEMORY_BACKUP_POLICY_ACKNOWLEDGED':'false','MEMORY_ALLOW_REAL':'false','MEMORY_AUTOMATIC_CAPTURE':'false','TELEMETRY_DISABLED':'true',
         'LITELLM_LOCAL_MODEL_COST_MAP':'True','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1',
         'HF_HOME':'/models','HF_HUB_CACHE':'/models/hub','ALLOW_HTTP_REQUESTS':'false',
         'MEMORY_EMBEDDING_PATH':'/models/hub/models--qdrant--bge-small-en-v1.5-onnx-q/snapshots/aa8f8b060edb00e03bfdd08813a2949946c8ba55'}
    container={'name':'choms-memory','image':IMAGE,'imagePullPolicy':'Never',
        'command':['/src/.venv/bin/python','/app/server.py'],'workingDir':'/src',
        'env':[{'name':k,'value':v} for k,v in env.items()]+[{'name':'DB_PASSWORD','valueFrom':{'secretKeyRef':{'name':'choms-memory-runtime','key':'database-password'}}}],
        'ports':[{'name':'mcp','containerPort':8080}],
        'resources':{'requests':{'cpu':'250m','memory':'1Gi'},'limits':{'cpu':'1','memory':'3Gi'}},
        'securityContext':{'runAsNonRoot':True,'readOnlyRootFilesystem':True,'allowPrivilegeEscalation':False,'capabilities':{'drop':['ALL']}},
        'startupProbe':{'httpGet':{'path':'/ready','port':'mcp'},'periodSeconds':5,'timeoutSeconds':3,'failureThreshold':36},
        'readinessProbe':{'httpGet':{'path':'/ready','port':'mcp'},'periodSeconds':10,'timeoutSeconds':3},
        'volumeMounts':[{'name':'code','mountPath':'/app','readOnly':True},{'name':'auth','mountPath':'/auth','readOnly':True},
                       {'name':'state','mountPath':'/state'},{'name':'tmp','mountPath':'/tmp'},
                       {'name':'models','mountPath':'/models','subPath':'models-76fb6636f317812a','readOnly':True}]}
    objects=[{'apiVersion':'v1','kind':'ServiceAccount','metadata':meta('choms-memory-adapter'),'automountServiceAccountToken':False},
        {'apiVersion':'v1','kind':'PersistentVolumeClaim','metadata':meta('choms-memory-state'),
         'spec':{'accessModes':['ReadWriteOnce'],'storageClassName':'choms-memory-local','resources':{'requests':{'storage':'1Gi'}}}},
        {'apiVersion':'v1','kind':'Service','metadata':meta('choms-memory'),'spec':{'type':'ClusterIP','selector':labels,
         'ports':[{'name':'mcp','port':8080,'targetPort':'mcp'}]}},
        {'apiVersion':'apps/v1','kind':'Deployment','metadata':meta('choms-memory'),
         'spec':{'replicas':1,'strategy':{'type':'Recreate'},'selector':{'matchLabels':labels},
          'template':{'metadata':{'labels':labels,'annotations':{'choms.platforms/source-sha256':digest}},
           'spec':{'nodeSelector':{'kubernetes.io/hostname':'choms-node-02'},'serviceAccountName':'choms-memory-adapter',
            'automountServiceAccountToken':False,'terminationGracePeriodSeconds':45,
            'securityContext':{'runAsNonRoot':True,'runAsUser':1000,'runAsGroup':1000,'fsGroup':1000,
             'fsGroupChangePolicy':'OnRootMismatch','seccompProfile':{'type':'RuntimeDefault'}},
            'containers':[container],'volumes':[{'name':'code','configMap':{'name':code}},
             {'name':'auth','secret':{'secretName':'choms-memory-runtime','defaultMode':288}},
             {'name':'state','persistentVolumeClaim':{'claimName':'choms-memory-state'}},
             {'name':'tmp','emptyDir':{'sizeLimit':'128Mi'}},
             {'name':'models','persistentVolumeClaim':{'claimName':'cognee-data','readOnly':True}}]}}}},
        {'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta('choms-memory-isolation'),
         'spec':{'podSelector':{'matchLabels':labels},'policyTypes':['Ingress','Egress'],'ingress':[],
          'egress':[{'to':[{'podSelector':{'matchLabels':{'app.kubernetes.io/name':'postgresql','app.kubernetes.io/part-of':'choms-memory'}}}],
                     'ports':[{'protocol':'TCP','port':5432}]},
                    {'to':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'kube-system'}},
                            'podSelector':{'matchLabels':{'k8s-app':'kube-dns'}}}],
                     'ports':[{'protocol':'UDP','port':53},{'protocol':'TCP','port':53}]}]}},
        {'apiVersion':'networking.k8s.io/v1','kind':'NetworkPolicy','metadata':meta('choms-memory-to-postgresql'),
         'spec':{'podSelector':{'matchLabels':{'app.kubernetes.io/name':'postgresql','app.kubernetes.io/part-of':'choms-memory'}},
          'policyTypes':['Ingress'],'ingress':[{'from':[{'podSelector':{'matchLabels':labels}}],
                                             'ports':[{'protocol':'TCP','port':5432}]}]}}]
    return yaml.safe_dump(config,sort_keys=False),yaml.safe_dump_all(objects,sort_keys=False)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--rollback',action='store_true')
    args=parser.parse_args()
    code,resources=render()
    if args.rollback:
        deployment=next(o for o in yaml.safe_load_all(resources) if o['kind']=='Deployment')
        deployment['spec']['replicas']=0
        print(yaml.safe_dump(deployment,sort_keys=False),end='')
    elif args.check:
        assert (DEST/'central-code.yaml').read_text()==code,'central_code_stale'
        assert (DEST/'central.yaml').read_text()==resources,'central_manifest_stale'
        print('MEMORY_RENDER_CHECK_PASS')
    else:
        (DEST/'central-code.yaml').write_text(code)
        (DEST/'central.yaml').write_text(resources)
