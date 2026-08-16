# Architecture Decision Records

Architecture Decision Records (ADRs) preserve decisions that affect multiple
tasks or constrain future implementation.

## Format

Use the next four-digit sequence and a short kebab-case name:

```text
NNNN-short-decision-name.md
```

Each ADR contains:

- **Status:** `proposed`, `accepted`, `superseded`, or `deprecated`.
- **Context:** the problem and verified constraints.
- **Decision:** the rule being adopted.
- **Consequences:** benefits, costs, risks, and operational implications.
- **Evidence:** links to versioned implementation or validated documentation.

Create an ADR only for a durable architectural decision. Operational outcomes
belong in [`WORKLOG.md`](../context/WORKLOG.md); current facts belong in
[`CURRENT_STATE.md`](../context/CURRENT_STATE.md). Never rewrite an accepted
ADR to hide history. Add a superseding ADR and link both records.

ADRs must not contain Secret values, credentials, personal data, backup
contents, or unnecessary sensitive topology.
