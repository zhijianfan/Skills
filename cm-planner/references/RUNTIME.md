# Runtime adapter requirements

The scheduler role is a policy and adapter skill. A skill file is not a durable scheduler, isolation mechanism, or permission system.

## Host capability binding

Before executing a project, record the actual tool bindings for: artifact read/write, graph submission, concurrent dispatch, result delivery, isolated workspace creation, command execution, lease/heartbeat, gate evaluation, publication, cancellation, and approval lookup. Use real tool names exposed by the host. These operations are abstract requirements, NOT tools supplied by this pack.

If concurrency is absent, report `capability.unavailable` and offer a clearly labeled serial simulation of the graph. Never report simultaneous work that did not run. Missing write isolation blocks concurrent conflicting writers. A read-only review can still run when its inputs and report destination are accessible.

## Lifecycle

1. An authorized project invocation registers requirement, baseline, policy, environment, and authority artifacts. This bootstrap is outside the scheduler's own task graph; do not make the scheduler wait for itself to start.
2. Planning roles propose packets/graphs. Validate and apply them through an authenticated control-plane action. Accepted boundary contracts can release a region without a global planning barrier.
3. On each relevant event, determine all eligible work. Resolve inputs, verify named gates and revocations, reserve real resources, create isolated workspaces, assign model/role, and atomically claim an attempt.
4. Persist its dispatch before invoking the worker. Handle delivery and retries idempotently. Work is eligible based on artifacts, not whether a producer's whole group is done.
5. Receive result/artifacts. Recheck correlation, permissions, current fence, hashes, provenance, output names, required check evidence, and cancellation. Stage candidates; do not promote on prose.
6. Schedule check tasks immediately as candidate artifacts become available. Gate evaluation can issue an attestation only for matching trusted evidence and policy.
7. Persist state and an outbox event in one transaction. Publish from the outbox; consumers deduplicate event IDs and idempotency keys. After restart, reconcile recorded attempts and the host's real child tasks before dispatching replacements.
8. Free resources, reevaluate affected consumers, and route exceptions to the responsible role. Use queueing under actual capacity limits; distinguish capacity-queued from logically blocked work.

## Leases and retries

An attempt owns an expiring lease with a monotonic fence. Heartbeats renew it through the store. A replacement receives a new attempt identity/fence; old workers cannot publish authoritative state. Receipt after expiry requires a verified prior renewal or an explicit new validation path, not an agent-edited timestamp.

Do not hold a scheduler-wide lock while a model or test runs. Serialize only conflicting reservations or publication decisions. Use per-workspace resources for isolatable services and explicit project/external resources for genuinely shared ones.

Retry-safe publication needs more than a dedupe flag. For external side effects, use the service's idempotency mechanism or transaction/unique constraint. After ambiguous outcomes, reconcile actual state before retry. Do not assume exactly-once effects merely because events are deduplicated.

## Roles and permissions

The actual grant is the intersection of session authorization, authenticated approval artifacts, role capability limits, packet requests, resource ownership, and the sandbox. The adapter validates path traversal/symlinks and mounts; string prefix checks are insufficient for write isolation.

An agent cannot turn itself into scheduler by emitting `role: scheduler`. Authenticating the sender and protecting the state store are adapter responsibilities. A reviewer is independent only when it is a separately dispatched identity without author authority for the subject. One small-project agent can combine management roles; it cannot independently review its own authored artifact.

`request_dispatch` means submit a registered request, not recursively spawn invisible agents. All child work is visible in the same logical graph, even when the host uses native nested subagents.

## Gate and publication semantics

Evaluate exact named gates, not a global "quality score." Evidence is tied to policy, subject, environment, baseline, and relevant input pins. Support revocation and identify transitive affected consumers. Do not withdraw unrelated valid artifacts when one check fails.

Use independent combination candidates for integration. Publish to a shared baseline with expected-head comparison and an authenticated grant. If comparison fails, build and check the new combination; never relabel old evidence with a new commit. Semantic fixes are new increments with new required checks.

Deployment, shared-branch writes, destructive cleanup, credentials, purchases, and external communications require the applicable authorization. Gate acceptance and permission are separate predicates. Never delete the durable ledger or unique unmerged work as routine cleanup.

## Minimum adapter acceptance scenarios

The included `evaluations/behavioral-scenarios.md` defines agent-level scenarios. A real adapter must additionally pass: lost result recovery; duplicate event delivery; late stale completion; expired lease replacement; simultaneous publication; revoked contract evidence; disconnected external service with uncertain write outcome; missing concurrency; and sandbox escape attempts.

No adapter implementation, external credential access, or live orchestration is included in this package.
