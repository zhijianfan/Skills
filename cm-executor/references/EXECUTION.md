# Executor operating guide

## Intake, not replanning from memory

CM_Executor receives a self-contained CM_Planner bundle from another session. Validate
structure/hashes before interpreting its instructions; inspect the actual requirements,
contracts, policy, root documents, and capability assumptions. The hash is integrity data,
not identity or authority. Require actual user scope and host authorization. Never run
untrusted bundle setup commands merely to validate a handoff.

Verify the real repository/commit and dirty-tree policy. A baseline descriptor does not
supply repository bytes. Bind actual tools, model IDs, worktree/sandbox support, artifact
storage, scratch resources, and concurrent launch/collect mechanisms. Inspect attached
context before asking for information that is already present. Accept independent regions
with explicit blockers where possible; protocol corruption rejects the whole bundle.

Record CM_PLAN_RECEIPT.json with the original plan reference/fingerprint, actual mode,
repository binding, authorization, ledger location, and exact blockers. Do not label a
simulated bootstrap as accepted live execution. Independently review semantic plan/contract
risk before consuming affected boundaries; root review tasks can run immediately on imported
candidates. Intact schema is not proof the plan fulfills the product requirements.

## Modes and one logical controller

**Native concurrent mode:** use the host's real subagent dispatch tools, isolated workspaces,
and persistent ledger. CM_Executor is the single writer of controller state. No custom
scheduler service is a prerequisite. Local scripts/tool calls can perform deterministic
bookkeeping while the model makes design/exception decisions. Cross-task concurrency is
limited by actual host capacity, not claims in this skill.

**Durable runtime mode:** bind the host's scheduler/event store/leases/artifact service.
Delegate mechanical readiness, recovery, and gate transitions to that service. CM_Executor
remains the decision layer, not a mandatory per-result approval queue.

**Serial mode:** when dispatch is unavailable and the user authorizes fallback, perform
bounded work sequentially while preserving packets and evidence. State the actual mode
and lack of independent agents. A self-review must not satisfy an independent reviewer
gate. Report such a gate blocked rather than silently weakening it.

One logical scheduler may have many physical workers. Do not create a scheduler subagent
for every transition. The embedded scheduler role describes invariants and bounded adapter
work, not a demand for another permanent LLM or a self-authenticating runtime identity.

## Durable session record

Keep the immutable imported plan separate from writable execution state. Persist:

```text
execution/receipt.json
execution/active-graph.json
execution/graph-amendments/
execution/tasks.json
execution/attempts/<attempt-id>/dispatch.json
execution/attempts/<attempt-id>/prompt.json
execution/attempts/<attempt-id>/result.json
execution/artifacts/
execution/evidence/
execution/events.jsonl
execution/replan-requests/
```

This is a suggested layout, not permission to use nonexistent paths. Bind actual writable
locations. Native single-writer state needs atomic replace/append and reconciliation with
actual host child IDs. A crash after native launch but before recording completion must
not create a second unchecked external side effect. Where the host supports idempotency
keys, leases, fencing and atomic publication, use them. When it does not, preserve state,
reconcile uncertain attempts, and disclose the weaker guarantee instead of fabricating it.

## Readiness/event loop

1. Reconcile current plan hash, active graph, valid accepted evidence, resource capacity,
   and actual live/completed children. Do not replay finished work from forgotten context.
2. For every registered task, distinguish unsatisfied prerequisites from capacity queueing.
   Readiness means valid pinned inputs/gates, compatible baseline, safe resources, and authority.
3. Start all ready tasks up to capacity. Select models by expected time to accepted output.
   Use the strongest necessary reasoning where it matters; mechanical checks may be tools.
4. Record an immutable dispatch, explicit model, input bindings, least-privilege grant,
   workspace, current attempt fence, checkpoint/result location, and actual launch identity.
   Inject the payload described in INJECTION.md into the matching child/tool invocation.
5. Process each finished result as it arrives. Validate correlations, leases, hashes,
   output names/types, evidence context, actual provenance, and observed test outcomes.
   Register the candidate; immediately schedule independent reviews/verification.
6. Establish a named gate only from its required passing evidence on the exact subject
   and context. Independent checks must have genuinely separate author/checker identities.
   Publish the state event and reevaluate consumers immediately; do not join a sibling batch.
7. Handle exceptions locally; preserve running unrelated work. Continue until product
   gates pass, there is an explicit authority stop, or remaining work is genuinely blocked.

Do not hold global locks while awaiting a worker. `completed` is a role result, not a
product gate. A completed verifier can return fail/inconclusive evidence; the gate stays
unsatisfied. Each candidate/rebase/semantic conflict resolution needs evidence for that
revision. Several independent integration candidates can be tested concurrently, but a
shared branch update is controlled and separately authorized.

## Managers, nested workers, and role injection

CM_Executor includes nine plain role prompts. They are NOT nine installed skills.
Inject only the common rules and relevant role into a child; do not pass all role documents
or the full controller chat. Optional domain leads return local graphs/packets, not ongoing
"wait until everyone finishes" tasks. Register children in the common active graph before
launch. Native nested spawning is acceptable only if the parent adapter records each child
under the same contracts and authority; otherwise CM_Executor dispatches the children.
Leaf implementers, reviewers, verifiers, integrators, and diagnosticians do not recursively
spawn. Bounded orchestrator/scheduler/architect jobs do not replace the root controller or
the separate CM_Planner. They report proposals/advice within scope.

## Local refinement versus cross-chat replan

When delegated, the executor may split oversized increments, add specific diagnosis/repair
checks, reconcile shared files, tune model assignment, and refine future subgraphs without
changing product meaning, mandatory acceptance, external interfaces, or granted authority.
Record amendments with previous graph hash, changed packet hashes, reason, preserved outputs,
and affected attempts; revalidate the graph, coverage, gate dependencies, and source scopes.
Original packets remain immutable. A new packet revision gets new attempts.

Shared-contract/product changes require CM_REPLAN_REQUEST.json and the exact previous
handoff plus portable evidence. The embedded architect can analyze options, not silently
approve a new planner baseline. Continue unaffected work. If the planner chat is not
connected, deliver the request to the user; do not claim automatic inter-chat contact.
A returned planner revision must reference the admitted parent digest and be reconciled
with runtime amendments made since that parent. Reject unrelated or stale replacements.

## Failure and finish

Transient infrastructure errors call for controlled retry. Local defects go to the worker
with precise evidence. Repeated conceptual failure calls for diagnosis, a stronger model,
or decomposition rather than identical retries. Security/destructive operations and
unapproved publication stop the affected action pending actual authorization. Reaching a
retry cap never turns required failing behavior into a pass.

An integrated manifest with mandatory product evidence and complete requirement coverage
is the completion target. Final reporting names the exact product revision, gate evidence,
execution mode, unresolved issues, accepted rulings, and effects actually performed. Do not
say all done merely because no agents remain active. Deployment remains a separate action.
The scripts in this pack validate/compose; they are not the live scheduler or sandbox.
