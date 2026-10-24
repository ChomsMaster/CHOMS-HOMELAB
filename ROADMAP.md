# CHOMS Platforms roadmap

Local evidence updated 24 October 2026. Runtime facts remain the dated inventory;
no fresh cluster, backup or deployment verification was performed in this work.

| Area | Implemented evidence | Still pending |
|---|---|---|
| Portfolio | Independent public snapshot; working notes archived | Owner presentation review |
| Validation | Shared local/CI entry point and advisory security backlog | A verified green remote CI run |
| Recovery tooling | Public-recipient-only age exporter; 22 synthetic tests passed | Real kit, controlled restore, payload authenticity and measured RPO/RTO |
| Recovery custody | Local encrypted-artifact contract and commit guard | Independently verified offsite copy and operational acceptance |
| Kubernetes isolation | Policies drafted for 13 public namespaces | CNI/flow tests and staged rollout |
| Terraform / Helm | Versioned values, locked releases and import-first code | Reviewed imports and adoption; no apply performed |
| Ansible | Node baseline | Complete provisioning/rebuild evidence |
| Runtime security | Documented per-workload hardening and accepted risks | Remaining device isolation, image pins and operational checks |
| GitOps / resilience | Procedures and architecture documented | Reconciliation, justified HA design and service objectives |

Priorities: validate remote CI, review workload-specific security debt, test
NetworkPolicies in controlled scope, adopt IaC ownership and prove recovery.
Keep capture, export, restore and publication as separate authorized operations.
Do not treat code completion or synthetic encryption as operational recovery.

The [detailed backlog](docs/context/ROADMAP.md) retains dated historical outcomes;
it is not the deployment authority.
