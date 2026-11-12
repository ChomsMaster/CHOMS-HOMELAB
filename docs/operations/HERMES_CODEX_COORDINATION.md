# Hermes → Codex coordination on node-dev-02

## Prepared implementation

`tools/choms-coordinator/SKILL.md` defines the Hermes workflow. The MCP server in
`scripts/coordination/choms_coordinator_mcp.py` provides `delegate`, `status`,
`result`, `checkpoint`, and `cleanup`. It starts the installed Codex CLI with
`codex exec --ephemeral --json --profile omniroute`; it never resumes or replaces
an existing Codex session, launches no shell, commits nothing, and publishes
nothing. Workspaces must be Git directories below the configured project root.
Dirty worktrees, concurrent jobs for one workspace, and paths naming CHOMS-Bios or
CHOMS BoardView are rejected. The task and result ledger is private (0700
directory, 0600 files); cleanup only
removes one terminal job record and requires `explicit=true`.

The coordinator requires a Codex profile named `omniroute`. The inspected Codex
configuration has no profiles, so this precondition is currently unmet; even
after creating the profile, it would not prove that the authorized OmniRoute
route is configured.
The MCP `checkpoint` tool requires `user_authorized=true`, a successful job, and
the existing CHOMS Memory bridge. It calls only the established `checkpoint`
operation, with the existing client identity. A successful Codex result is not
automatically copied to memory. Memory's live policy must accept the write;
currently `real_memory_allowed=false` and `backup_policy_approved=false`, so real
work checkpoints remain blocked. The fixture-only acceptance path is separate.

## Current verification and blockers

- CHOMS Memory health read through the current authenticated connector: `ready`,
  automatic capture off, real memory off. An isolated project fixture completed
  propose → approve → read-by-ID → search → checkpoint → read checkpoint → forget;
  health confirmed no canonical rows, vectors, graph artifacts, or content receipts.
- CodeBase Memory initially listed zero projects. A temporary fixture under this
  repository was indexed (20 nodes/19 edges), searched with source readback, then
  deleted; a follow-up project listing confirmed it was gone.
- The coordinator state machine and exact-content inventory passed six local
  tests using a fake Codex executable. This verifies job isolation, status/result,
  cleanup, path/profile rejection, and hash deduplication. It does not verify a
  real Hermes invocation or real Codex inference.
- The repository's Hermes verifier was corrected to parse the existing YAML
  config and its underscore server name. Its native discovery registered 0/8
  tools because Hermes' active `safe_worker` policy refuses to spawn MCP
  subprocesses in this execution context. That guard was not disabled; no Hermes
  Memory fixture was written. This proves the current process cannot verify or
  use Hermes MCP here.
- Hermes currently reports provider `nous`; its existing configuration and
  available backup were not changed. The authorized OmniRoute endpoint and key
  could not be inspected from the live cluster: `kubectl` has no usable current
  context in this environment. No endpoint or key was printed, guessed, or
  written to a profile. The actual Hermes→OmniRoute profile and live delegation
  test are therefore pending.
- The current ChatGPT Work session exposes neither the iMac's local MCP process
  nor a connected CHOMS coordinator. No account plugin or service was published.

## Local MCP configuration after the endpoint/profile gate

Register only after an operator verifies the `omniroute` Codex profile and the
existing Memory bridge target. Keep the target and credentials in the private
local MCP configuration/environment; do not paste them into Git or a task:

```yaml
mcp_servers:
  choms-coordinator:
    command: python3
    args:
      - -I
      - /path/to/choms-homelab-public/scripts/coordination/choms_coordinator_mcp.py
      - --workspace-root
      - /path/to/authorized/project
      - --state-dir
      - /path/to/private/state/choms-coordinator
```

Replace paths locally. Do not use a project root that includes CHOMS-Bios or
CHOMS BoardView. The coordinator reads the `--ssh-target` argument from the
already registered `choms_memory` entry at runtime, validates its shape, and
invokes the existing fixed-command SSH wrapper. It does not copy the target into
a second config. Do not rotate, copy, or print any client credential.

## OmniRoute and Nous recovery

The current Hermes configuration still points to Nous Portal. No provider,
model, session, auth file, endpoint, or Kubernetes resource was changed here, so
the existing configuration remains the recovery source. Before a future local
edit, make a private, permission-restricted backup of the exact Hermes config and
record its SHA-256 without displaying its contents. Use only the endpoint and
authentication mechanism confirmed from the live OmniRoute configuration; the
OmniRoute API requires its own client key even when the Codex app-server provider
uses ChatGPT account auth. Do not substitute the sidecar WebSocket endpoint for
the authorized API route.

## ChatGPT Work MCP point

ChatGPT desktop/local Codex clients can run local stdio MCP servers. Hosted
ChatGPT Work uses a plugin with remote MCP tools; OpenAI's current flow uses
Plugin Creator and Sites to host and publish that plugin, and requires the Site
owner's account permissions to publish. This task did not publish a service or
plugin. The external account owner must choose an approved private relay or
hosting boundary and complete plugin creation, authentication, publishing, and
installation; account/workspace permissions must be confirmed there. Keep the
plugin's API access narrow and authenticated. Never expose the internal
OmniRoute or Memory service directly. See [OpenAI MCP and Plugin Creator
guidance](https://learn.chatgpt.com/docs/extend/mcp).

## Install, operation, and recovery

After the implementation is published from a clean, synchronized Git state,
use the existing workstation source/apply workflow. First back up the Hermes
configuration privately; run check/plan, inspect all proposed deltas, and apply
only the plan with zero conflicts. Add one coordinator skill/MCP entry without
replacing other entries. From Hermes, submit one bounded task, poll its job ID,
recover the terminal result, inspect the resulting diff, then request the
checkpoint only when the user authorized it and CHOMS Memory accepts it.

On a failed worker, preserve the job record for diagnosis and do not resubmit if
the task may already have changed files. Restore the private configuration
backup only if a future edit is actually made; the reversible coordinator
cleanup removes only its exact job record. No rollback of OmniRoute, Kubernetes,
OAuth, Codex sessions, or unrelated skills is part of this procedure.

OpenHands remains `BLOCKED_ISOLATION_CONTRACT`. BIOS/BoardView, Kubernetes
permissions, service publication, and credentials remain outside this block.
