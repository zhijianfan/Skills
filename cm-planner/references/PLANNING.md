# Planner operating guide

## Goal and scope

Minimize elapsed time until the integrated product satisfies fixed acceptance standards.
Abundant agents remove a capacity limit, not genuine dependencies, context transfer,
shared hardware, external approvals, or correctness obligations. Do not promise an optimal
schedule merely because the graph is wide. Identify the longest chain and shorten real
bottlenecks without delaying independent ready work.

The planner is a design/review model in a separate conversation. It can inspect available
repository and document context, write contracts/fixtures and planning artifacts, and
validate the handoff. It does not need to install CM_Executor, know its exact model names,
invoke worker tools, write product implementation, or remain online during normal execution.

## From requirements to a runnable frontier

Snapshot user requirements, decisions, versions, relevant excerpts/attachments, acceptance
criteria, platform constraints, performance expectations, setup requirements, and source
baseline. Say which repository facts were actually verified and which require executor
verification. Preserve already settled answers. Do not use hidden chat history as context.

Define semantic boundaries before internal procedures: inputs/outputs, nullability,
error behavior, ordering, concurrency, atomicity, invariants, formats, compatibility, and
ownership. Publish the minimum coherent set needed by one region; no all-planning-finished
barrier. A contract fixture/mock is a local substitute, never proof of real integration.

Assign requirement IDs and map every requirement to implementation and acceptance packets.
Nonfunctional requirements need measurable acceptance too. A plan that covers happy paths
but never checks concurrency, failure semantics, or product-level outcomes is incomplete.

For each task ask: what exact artifact/evidence makes this task possible? Contracts can
unblock UI and backend implementation together. Actual implementation is needed by linking,
integration, and real-system tests. Test authoring and test execution are separate tasks
when that enables earlier progress. Group membership and earlier task numbers are not edges.

Use coherent increments; keep a worker's local edit-test-debug loop together. Split where
outputs can be accepted separately or release useful consumers sooner. A group manager is
optional and returns bounded subgraphs, not serial approvals or private worker trees.

## Packet authoring

Use the bundled `cdag/1.0` schema, not an improvised numbered task list. All planned tasks
have the same packet shape. Use `architect`, `domain-lead`, `implementer`, `reviewer`,
`verifier`, `integrator`, `diagnostician`, or bounded `orchestrator`/`scheduler` roles.
`roles.json` describes output types and permission ceilings; it is not an installation list.

Each packet specifies objective and requirement IDs, exact consumers/producers, reasons
for edges, permitted and protected paths, shared resources, required checks and expected
results, output names, acceptance policy pin, delegation, and recovery. Symbolic outputs
are `{producer_task, output_name}`; actual external payloads use immutable artifact refs.
Real workspaces, host model IDs, actual grants and leases belong to executor dispatches.
Use no `/mnt/data/...`, private chat links, or planner machine paths as product dependencies.

For unelaborated future scope, write a real domain-planning packet producing a reviewed
subgraph. Preserve requirement coverage and explicit boundaries; do not emit fake runnable
implementation placeholders. The executor can apply the subgraph only within delegated
scope, recording an active-graph revision and validating all dependencies and gates again.

## Gate placement and self-check

Root contracts are candidates. Include read-only root-review packets that consume them
with an empty gate list. Their produced evidence can satisfy the contract's acceptance
gate; dependent implementation then becomes ready. Code reviews likewise consume candidates.
Check the graph with these proof edges included, not just producer/output edges.

Every final required gate must have canonical scheduled check producers for the exact
combined output. Avoid a final gate requiring itself. Integration publishes a combination
candidate; independent tests/review establish its gate; separately authorized publication
can consume that gate. No acceptance state is inferred merely from `completed` task status.

Check shared-file ownership (registries, lockfiles, manifests), test-resource isolation,
missing producers, unknown outputs, contradictory interfaces, missing inputs, cycles,
complete requirement coverage, and retained product authority. Estimate bottlenecks using
explicitly labeled assumptions, not fake timing measurements.

## Packaging and validation

Create a bundle with `HANDOFF.json` plus listed portable documents. Use the full example
in the distribution as a structural reference, not as a real executable project. It is
marked `example: true` and deliberately rejected by live validation. Do not remove that
flag without replacing all synthetic requirements, baselines, commands, and context.

The shared schema is authoritative. `seal` recomputes file checksums and records the
installed contract fingerprint; it does not recompute changed graph artifact pins, invent
missing fields, grant approval, or manufacture evidence. When a root payload changes,
update its root hash and all graph references deliberately before sealing.

```bash
python scripts/handoff.py seal /path/to/plan-bundle
python scripts/handoff.py validate /path/to/plan-bundle --live
python scripts/handoff.py pack /path/to/plan-bundle --output /path/to/CM_PLAN.zip --live
```

Give the other chat the complete ZIP/directory and manifest SHA-256. Include a brief
summary of objectives, baseline, ready regions, blockers, and acceptance. Stop after delivery.
A new plan is not implementation authorization and not evidence that tests passed.

## Replan input

CM_REPLAN_REQUEST.json must be accompanied by its exact prior handoff and referenced
supporting evidence. Validate its protocol/fingerprint and parent reference. Address the
specific question; preserve unrelated decisions and compatible completed work. Product
choices return to the human rather than an invented planner preference. Return a complete
new plan revision with a parent digest, changed interfaces/packets, affected consumers,
migration/revalidation requirements, and the evidence that can still stand.
