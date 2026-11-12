# CHOMS Unified Skills — audit ingestion

`scripts/coordination/unified_skills_inventory.py` reads the audit under
`~/choms-skill-audit/`, verifies all 228 host source records against their
recorded SHA-256 and byte counts, then groups byte-identical copies by digest.
The generated [`INVENTORY.json`](INVENTORY.json) contains no absolute source
paths or skill bodies. The original source files remain untouched in their
existing locations. Fifteen content groups are exact duplicates across the two
host inventories; similar names or descriptions are not deduplicated.

Rebuild the metadata index with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 scripts/coordination/unified_skills_inventory.py \
  --output tools/choms-unified-skills/INVENTORY.json
```

The index is not an activation plan. All 213 unique skills remain blocked until
functional and security review is recorded for the exact hash. The `codex`
candidate is explicitly blocked in [`REVIEW_DECISIONS.json`](REVIEW_DECISIONS.json):
its instructions recommend approval bypass/full access and include external
publishing and broad cleanup examples. No audited skill from this catalog was
activated by this block. Do not import source bodies into the public repository;
source licenses and executable/plugin behaviors remain subject to review.
