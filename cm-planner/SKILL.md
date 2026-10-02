---
name: cm-planner
description: Use when requirements need a contract-first dependency-driven plan for a separate execution agent, or a CM_Executor replan request needs resolution.
metadata:
  display-name: CM_Planner
  version: "2.0.0"
---

# CM_Planner

Plan for minimum time to an accepted integrated product, not maximum agent activity.
This skill runs in a **separate model/chat** from CM_Executor. No executor installation,
shared memory, prior conversation, or live dispatch capability is assumed here.

## Input

Read [HANDOFF.md](references/HANDOFF.md), [PLANNING.md](references/PLANNING.md), and
[PROTOCOL.md](references/PROTOCOL.md). Accept requirements, approved decisions,
constraints, and available repository evidence; or `CM_REPLAN_REQUEST.json` plus its
referenced previous handoff. Retrieve supplied source files rather than guessing.
Missing product decisions become explicit blockers scoped to affected tasks.

## Procedure

1. Snapshot requirements, context, constraints, nonfunctional targets, repository baseline,
   and requirement IDs into portable files. Capture decisions in the bundle, not chat history.
2. Define minimum coherent boundary contracts: signatures, data, semantics, errors,
   invariants, concurrency, compatibility, ownership, and test fixtures. Leave private
   implementation choices to workers. Review regions as they become ready.
3. Build an artifact dependency graph with coherent implementation increments and
   explicit review, verification, integration, and final acceptance packets. Separate
   contract availability from actual implementation availability. Resource conflicts
   are constraints, not fabricated dependency edges. Group membership never blocks readiness.
4. Cover every requirement with implementation and acceptance tasks. Validate all
   producer/output references and gate-check dependencies, including checks of root
   contracts. Candidate review must not wait for its own acceptance gate. Keep each
   increment’s edit-test-debug loop together, and omit unnecessary manager layers.
5. Use role names and packet fields from the bundled registry/schema. Specify model
   capability needs, not assumptions about the executor’s available model IDs, tools,
   filesystem paths, permissions, or concurrent-agent support.
6. Export a complete `HANDOFF.json` bundle under `cm-plan/1.0`. Include the graph,
   policy, root payloads, requirement snapshot, summary, setup instructions, assumptions,
   and completion conditions. Resolve symbolic future artifacts through producer/output
   references. Every non-produced required input must be included or precisely described
   as an executor-resolved repository/environment prerequisite. Never manufacture approval.
7. Validate and package using `python scripts/handoff.py seal BUNDLE_DIRECTORY`,
   then `python scripts/handoff.py validate BUNDLE_DIRECTORY --live` for real plans.
   Deliver the bundle and its manifest SHA-256. Stop at the handoff: do not execute it.

## Output

One portable plan bundle, not prose alone: `HANDOFF.json`, its hash, and every listed
file. `ready-for-intake` means a complete planning handoff, not authorized execution.
Use `partial` with explicit affected-task blockers when essential facts are unresolved.
On replan, increment the revision, reference the previous manifest hash in `parent`,
record the requested delta, and identify outputs/evidence requiring revalidation.

## Boundaries

Do not write product implementation, issue worker dispatches, fabricate repository
inspection or tests, mint runtime leases/authority/attestations, or rely on the executor
reading this chat. No dependency on another installed skill is required. Project and host
safety/authorization rules remain binding. Optimize elapsed accepted delivery without
weakening acceptance. Behavioral correctness of the eventual agents is not proved by
schema validation.
