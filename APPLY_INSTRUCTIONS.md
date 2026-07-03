# Apply Instructions

This zip is a documentation update pack for `ChomsMaster/CHOMS-HOMELAB`.

## On the server

From the repository root:

```bash
cd /data/projects/choms-homelab
unzip /path/to/CHOMS-HOMELAB_CONTEXT_UPDATE_2026-07-03.zip -d /tmp/choms-doc-update
rsync -av /tmp/choms-doc-update/CHOMS-HOMELAB/ ./
```

Review changes:

```bash
git status
git diff -- CHOMS-HOMELAB_MASTER_CONTEXT.md PROJECT_STATUS.md SESSION_STATE.md ROADMAP.md docs/
```

Commit:

```bash
git add CHOMS-HOMELAB_MASTER_CONTEXT.md PROJECT_STATUS.md SESSION_STATE.md ROADMAP.md docs/
git commit -m "docs: update multi-node NAS context"
git push
```

## Notes

This pack updates documentation only. It does not change Docker Compose, services, firewall, or runtime configuration.
