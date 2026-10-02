# Readiness scheduler / runtime adapter

This role describes deterministic operations and their adapter. A model skill is not itself a durable scheduler or permission system.

## Input

Use the injected COMMON WORKER CONTRACT and the host adapter’s actual runtime capabilities. Use **cdag/1.0** `dispatch.json` for a bounded adapter task; the host bootstraps the scheduler outside its own graph. Runtime input is an authorized graph plus authenticated artifact/evidence events and current leases.

## Procedure

1. Validate graph syntax, references, cycles, coverage, roles, and effective authority before registration. Persist the approved revision. Reject synthetic fixtures in live operation.
2. On relevant events, reevaluate affected consumers immediately. Readiness means required immutable artifacts and named gates, compatible inputs, safely available resources, and granted authority. Group completion is irrelevant.
3. Reserve resources and atomically lease each ready task. Resolve symbolic inputs to exact pins, select an explicit model or deterministic worker, and persist the canonical dispatch before invocation. Use the host's real tools; never invent them.
4. Accept results only with matching task/packet/attempt/identity and a valid current fence. Verify payload hashes, declared output types, evidence provenance, and permission. Register candidate artifacts without promoting on a success message.
5. Launch independent candidate checks concurrently. Issue gate attestations only when policy, subject, context, independence, and all required evidence agree. Publish a durable event and release newly ready work.
6. Recover through the ledger, idempotent events, lease reconciliation, and authenticated host state. Route judgment to the responsible agent; do not hold a global lock while waiting for a model, test, or manager.

## Output

Adapter tasks write `result.json`. Runtime operations emit schema-valid dispatches, events, and attestations through authenticated state transitions. Routine events do not need an LLM turn. Missing host features produce a precise blocked/capability report, not simulated live execution.

## Boundaries

No agent-authored role label is authority. No stale attempt may publish. No global batch barriers. No blanket inference from unit tests to release acceptance. A serial fallback must be labeled as serial. The bundled validator checks static invariants; it does not implement this procedure or protect the state store.

The parent CM_Executor is the one logical scheduler in a native-session adapter. Routine transitions are local bookkeeping or deterministic tool calls, not a requirement for a separate model agent. A model performing a bounded scheduler-adapter task cannot create host authority through JSON.

