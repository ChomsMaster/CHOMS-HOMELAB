# CHOMS Platforms — Repository Instructions

CHOMS Platforms is the current project name. Historical paths and resources may
still use `choms-homelab`; do not rename them without a migration plan.

At the start of every task:

1. Read [`docs/context/CURRENT_STATE.md`](docs/context/CURRENT_STATE.md),
   [`docs/context/ROADMAP.md`](docs/context/ROADMAP.md), and the latest entries
   in [`docs/context/WORKLOG.md`](docs/context/WORKLOG.md).
2. Follow the detailed documents linked from those files.
3. Fetch Git, require a clean tree and `0/0` divergence, then verify the
   relevant Kubernetes runtime instead of assuming it matches Git.
4. Compare the authorized work with the roadmap and execute one workload or
   one logical block only.

Operational rules:

- Use one commit per logical change. Never create empty commits.
- For direct manifests, run local validation, server-side dry-run, and
  `kubectl diff` before applying. Never apply an unexpected diff.
- Change Helm workloads only through versioned values and the locked Helm
  workflow; never edit rendered resources directly.
- Validate rollout, storage, endpoints, and every known consumer. Roll back
  safely if validation fails. Do not declare success without evidence.
- Never print or commit Secret values, credentials, user data, dumps, or
  backup contents. Do not use broad destructive commands.
- Do not upgrade versions or packages, or change email, DNS, or router state,
  without a specific explicit task.

When a task changes project state, update `CURRENT_STATE.md`, append a concise
entry to `WORKLOG.md`, and update `ROADMAP.md` in the same logical commit.
Never rewrite historical worklog entries; append an explicit correction.
Finish by confirming service health, drift zero where applicable, a clean
tree, and synchronization with `origin/main`.
