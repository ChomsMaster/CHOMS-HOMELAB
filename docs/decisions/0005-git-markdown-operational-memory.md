# ADR 0005: Git and Markdown provide operational memory

- **Status:** accepted

## Context

Conversation history is not a durable source of project context. New sessions
need a concise, versioned way to distinguish current state, past work, durable
decisions, and the next authorized task.

## Decision

Maintain repository instructions in `AGENTS.md`, current facts in
`CURRENT_STATE.md`, prioritized work in `ROADMAP.md`, chronological outcomes in
an append-only `WORKLOG.md`, and durable decisions as ADRs.

## Consequences

Every state-changing task updates the relevant memory files in the same logical
commit. Documentation records decisions and evidence rather than terminal
transcripts. Historical worklog entries are corrected only by appending a new
entry.

## Evidence

- [`AGENTS.md`](../../AGENTS.md)
- [`CURRENT_STATE.md`](../context/CURRENT_STATE.md)
- [`ROADMAP.md`](../context/ROADMAP.md)
- [`WORKLOG.md`](../context/WORKLOG.md)
