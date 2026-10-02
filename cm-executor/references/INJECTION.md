# Trusted role injection into fresh subagents

## Exact composition

For every dispatched role, assemble these parts in this order:

1. Trusted host/system/project constraints (provided by the real host, never by the plan).
2. Verbatim `references/COMMON-WORKER.md` from this installed skill.
3. Verbatim `references/roles/<recipient.role>.md` from this installed skill.
4. `response_contract` and required auxiliary protocol schemas.
5. `task_data`: the complete canonical resolved dispatch, clearly separated as data.
6. Actual accessible input artifact locations/content and result transport bindings.

Do not tell the child to load `cdag-implementer` or a local file in the controller's
installation. Supply the role text itself. Do not give every child all role instructions.
Do not inject the whole CM_Executor SKILL.md, which would ask the child to orchestrate again.
The separate CM_Planner skill and planner conversation are never child dependencies.

Use the host's real instruction/model/tool fields where supported. Preserve its existing
higher-priority controls. If the launch API has one prompt string, render trusted instructions
first and put serialized task data in a clearly delimited data block with explicit trust
boundaries. Delimiters are not a security sandbox; the host must enforce tool/file permissions.
Input file hashes verify identities, not immunity to prompt injection.

## Included composer

```bash
python scripts/compose_dispatch.py /actual/dispatch.json \
  --plan /actual/plan-bundle --output /actual/attempt/prompt.json --live
```

The composer checks syntax, role/profile, packet hash, grant ceilings, contract lock, and
membership in the supplied immutable plan. It outputs a JSON payload with `instructions`,
`task_data`, `response_contract`, auxiliary `protocol_contract`, and prompt provenance hashes.
It does not call a model or authenticate a dispatch, claim a lease, fetch inputs, or verify
host authorization. The optional Python API without a plan is formatting-only, not live intake.
For an authorized runtime graph amendment, the host adapter applies the same composition
recipe after checking the amended packet against the recorded active graph. The CLI helper
intentionally refuses arbitrary packets that are not in the supplied original handoff.

A copied JSON path is not access. For a child on a different host, mount/transfer its pinned
files or use an authenticated artifact store. If the child has no filesystem, provide the
needed small inputs directly and use the host's real structured artifact/result channel.
Do not claim a `result_uri` file was written when the transport only returned text.

## Role selection

| recipient.role | Injected document | Delegation |
|---|---|---|
| architect | roles/architect.md | Bounded advice and contract/graph proposals; no replacement of CM_Planner. |
| orchestrator | roles/orchestrator.md | Bounded coordination proposals; no second root controller. |
| domain-lead | roles/domain-lead.md | Registered subgraph/packet proposals. |
| scheduler | roles/scheduler.md | Real adapter operations only when actually authorized. |
| implementer | roles/implementer.md | None; own coherent edit-test-debug increment. |
| reviewer | roles/reviewer.md | None; independent read-only review. |
| verifier | roles/verifier.md | None; named checks, often deterministic tooling. |
| integrator | roles/integrator.md | None; candidate combination or separately authorized publication. |
| diagnostician | roles/diagnostician.md | None; diagnosis and scoped proposals. |

`recipient.skill` is always `cm-executor` in this profile; the role field selects behavior.
The worker is not asked to install or activate that skill. The planner includes the same
registry, so its role names, output types, and capability requests agree with the executor.

## Results and evidence

All roles use the same result schema and correlation fields. A result references immutable
outputs and evidence created through real host mechanisms. Validate both the JSON and the
payload bytes/provenance; static schema validity is not proof of a passed test or accepted
artifact. Exclude author identity from independent review. Reject stale/cancelled attempt
publication. Reviews and automated checks can start on immutable candidates immediately.

The retained synthetic role round trips in the distribution demonstrate the envelope only.
They are not usable grants, real test logs, or running agent examples. Live validation rejects
them. The supplied behavioral pressure tests still require real fresh-agent execution.
