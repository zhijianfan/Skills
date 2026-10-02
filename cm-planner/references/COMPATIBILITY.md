# Compatibility and migration

There are exactly two discoverable skills: cm-planner and cm-executor. Display names are
CM_Planner and CM_Executor. The executor's role references are injected prompt modules,
not additional skills. Keep each whole skill directory intact; no sibling directory is needed.

The former cdag-* role skills are not required. Worker JSON keeps cdag/1.0 but uses the
CM profile's registry with recipient.skill=cm-executor. Old dispatches that name individual
cdag-* skills are not silently adopted. Convert deliberately and validate the new profile.
A bare old graph is not a portable CM handoff: add context, root payloads, a baseline,
acceptance/gate producers, a manifest, and genuine capability/authority intake.

CM_Planner does not invoke Superpowers' execution handoff or ask to choose an implementation
method in its own chat. It produces files for a different executor session. CM_Executor uses
the admitted graph rather than starting an initial brainstorming or planning cycle again.

When the user chooses the CM workflow for a project, select this project scheduling route,
not both this route and Superpowers' serial subagent-driven-development/executing-plans loop.
This is a workflow selection, not permission to override system, developer, user, security,
or mandatory project instructions. Keep required local engineering discipline (TDD, real
verification, scoped review, safe workspaces) and do not bypass it for speed. If a binding
higher-priority instruction actually prevents concurrent work, report that restriction.

No cross-chat memory or provider-specific model name is assumed. The planner declares needs;
the executor binds available models, tools, source, and authority. Missing tools lead to an
accurate capability report, not an invented dispatch. A plain chat without file/validation
tools must identify its output as an unvalidated draft; it must not invent files, hashes,
executed validators, or a ready-for-intake status. Real files can be mechanically sealed
and checked in the receiving environment before admission, without silently changing design.

The plan bundle is immutable after publication. Execution state lives elsewhere. Standalone
installs carry matching contract copies and reject version/fingerprint mismatches. Update
both installs together for a contract change; do not copy a new untrusted validator out of
an incoming plan and execute it to make validation pass.
