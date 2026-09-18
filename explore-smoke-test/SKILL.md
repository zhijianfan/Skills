---
name: explore-smoke-test
description: Use when running an Explore smoke test: score an agent's read-only repository exploration against concrete reference answers.
---

# Explore smoke test

An explicit repository-exploration diagnostic: run fresh, read-only agent sessions against a frozen repository snapshot, ask probes that demand concrete outputs, and score returned answers against reference answers derived directly from the repository. This is the cheap screening step before expensive long-context or agent-track benchmark runs (e.g. the Explore probes in the LocalCode-100K design, section 11). Not an always-run policy, a coding-task evaluation, or a speed benchmark.

## When to use

- Screening an agent/model's repository navigation before committing to full benchmark runs.
- Checking that a repository snapshot is explorable: every probe answer derivable from committed files alone.
- Comparing agent configurations (tool policy, prompting, context handling) on read-only retrieval.

Don't use for: measuring coding ability, any run where the session may edit files or execute tests/builds, or live debugging of a repository.

## Inputs and defaults

Resolve these from the operator's request; record the effective values in the report.

| Input | Default and meaning |
|---|---|
| `REPO_ROOT` | Current workspace. The tested sessions read only this repository. |
| `PROBE_SET` | At least 5 probes; record each with ID, question, tolerance rule, and reference evidence. |
| `RUNNER` | One fresh session per probe set. Prefer one-shot `hermes chat -q "..."`; a new WebUI session is equivalent. Never reuse a session across probe sets. |
| `TOOL_POLICY` | Read-only: `read_file`/`search_files` and read-only commands permitted; no writes, edits, git mutations, tests, builds, or network. State this in the injected prompt. |
| `OUTPUT` | `EXPLORE_SMOKE_TEST.md`, the sole deliverable. |

## Operating boundaries

Freeze the snapshot first: record `git rev-parse HEAD`, branch, dirty state, and capture time. Derive reference answers from this frozen state only. Do not modify the repository during the smoke test.

No leakage: reference answers, their evidence, and probe verdicts must never appear in a tested session's prompt, context, or shared memory. A session that could have seen them is contaminated — exclude it from scoring and say so. Do not feed probe answers into any coding or benchmark run; the Explore probes and the coding track are separate scoreboards.

## Probe authoring

Each probe must demand a concrete output, not an explanation. Working types:

- **Canonical ID** — the normalized identifier something resolves to.
- **Dependency chain** — an ordered list (e.g. target → its transitive dependencies).
- **Exact value** — a config setting, default, limit, version, or policy from the current docs/contracts.
- **Path/name** — which file owns a behavior or symbol.
- **Archive-vs-current** — what the current contract says versus a marked-archived or legacy implementation.

For each probe, derive the reference answer directly from the repository (read-only) before running anything, and record evidence: `file:line` or `file:section`. Predeclare the tolerance rule per probe:

| Rule | Applies to | Verdict |
|---|---|---|
| `exact` | one canonical string | ✅ only on exact match after whitespace trim |
| `set` | unordered list | ✅ only on same elements, any order |
| `ordered-chain` | dependency chain | ✅ only on same elements in same order |
| `any-of` | multiple acceptable forms | ✅ on any listed form |
| `canonical` | ID under the repo's normalization | ✅ only if normalization is applied as the repo defines it |

Baseline-check every probe: a fresh reader can answer it from committed files alone, with no prior conversation and no summary document. Require the set to span at least one shallow lookup, one cross-file chain, and one archive-vs-current distinction. Prose answers earn zero by rule; if a probe only admits prose, rewrite it until it demands a concrete output.

## Run

1. **Freeze.** Record revision, dirty state, and capture time.
2. **Derive.** Produce all reference answers and evidence from the frozen state (step above).
3. **Launch.** One fresh session per probe set. Inject only: repository path, the probe question, and the tool policy. No conversation history, no expected answers, no verdict hints.
4. **Capture.** Keep the full transcript, tool-call log, and model/runner identity for each session.

## Score

- Apply the probe's predeclared tolerance rule to the returned concrete answer. Nothing else counts.
- An answer that matches but has no supporting repository read in the transcript is `unverified` — it fails by default unless the operator predeclared otherwise.
- A contaminated session (possible answer-key exposure) is excluded, not scored.
- Record per-probe verdicts, then `solved / total`. Do not invent a numeric quality score; report solved counts and verdict evidence.

## Report

Write `EXPLORE_SMOKE_TEST.md` with:

```text
Probe | Expected (evidence) | Actual | Verdict
```

Then: solved/total, unverified and contaminated counts, runner/model identity, snapshot revision, and the most important remaining limitation (e.g. probe depth too shallow, transcript capture missing tool calls).

## Pitfalls

- **Leakage.** Expected answers placed anywhere a tested session can read them → contaminated run. Exclude and redo fresh.
- **Session reuse.** Cross-probe memory inflates later scores; one probe set per fresh session, always.
- **Prose credit.** Awarding a match for an explanation is the classic error; enforce the concrete-output rule at authoring time, not scoring time.
- **Unspecified tolerance.** Deciding "close enough" during scoring moves the target after the shot; predeclare `exact`/`set`/`ordered-chain`/`any-of`/`canonical` per probe.
- **Archive confusion.** Probes about legacy/rejected docs must state which document is normative; otherwise the tested agent cannot be wrong for following the marked archive.
- **Shallow probes.** If every probe is a one-file lookup, the test measures nothing; require the cross-file chain probe.

## Verification

- [ ] Snapshot revision and dirty state recorded before probing
- [ ] Every reference answer has `file:line` evidence from the frozen state
- [ ] Tested prompts contain no expected answers or verdict hints
- [ ] Each probe set ran in a fresh session; transcripts and tool logs captured
- [ ] Every verdict applied with the predeclared tolerance rule
- [ ] Report states solved/total and excludes contaminated sessions

## Source design

Derived from the LocalCode-100K repository coding benchmark design, section 11 ("Separate OpenCode/Hermes agent track"): optional read-only Explore probes run as separate fresh sessions, asking for concrete outputs, dependency chains, or canonical IDs with reference-derived expected answers; no reward for unsupported prose; probe answers never fed into the coding run.
