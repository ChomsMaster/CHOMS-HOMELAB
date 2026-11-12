---
name: choms-coordinator
description: Delegate a bounded task from Hermes to the installed Codex CLI, collect its result, and record an explicitly authorized CHOMS Memory checkpoint.
---

# CHOMS Coordinator

Use the existing Codex CLI from Hermes for a single bounded task when Codex is the requested worker. Keep the task, worktree, status, and result tied to one coordinator job ID.

## Preconditions

- Use the `choms-coordinator` MCP tools `delegate`, `status`, and `result`; do not invoke unreviewed third-party Codex skills.
- Select a workspace inside the configured project root. Preserve any pre-existing changes and sessions.
- The local Codex profile named by the coordinator must be the approved OmniRoute profile. If it is absent or cannot be verified, stop before delegating and report that gate.
- Do not pass API keys, OAuth material, private endpoints, or contents of auth/config files in task text.
- Never use `--dangerously-bypass-approvals-and-sandbox`, `danger-full-access`, `--approve-for-me`, or commands that publish, push, or modify unrelated projects.

## Delegation lifecycle

1. Call `delegate` with a bounded task and an authorized workspace. It returns a job ID and process state; it does not commit or publish changes.
2. Poll `status` by that job ID until it is `succeeded`, `failed`, or `cancelled`.
3. Call `result` only for a terminal job. Inspect the diff and verification evidence in the workspace before reporting completion.
4. Keep the result available for Hermes to use in this conversation. Do not copy it into memory automatically.
5. A CHOMS Memory checkpoint is allowed only when the user explicitly authorized that task's checkpoint and the Memory backup gate permits real writes. Otherwise report the checkpoint gate and retain the result only in the protected job record. Never switch to a fixture reference for real work.

## Recovery

- `status` is read-only. A failed job retains its exit code and bounded diagnostics.
- `result` is read-only. It does not resume or overwrite a Codex session.
- Remove a job only through its explicit cleanup operation after its result has been recovered. Cleanup never touches the workspace, Git history, client sessions, or credentials.
- If the worker loses its process or state record, stop and report the job ID. Do not replay a task that may already have changed files.
