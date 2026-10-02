# Acceptance map — synthetic only

contract-review: independent semantic review of the candidate API against requirements.
local-unit: worker's actual local regression cycle on its pinned candidate.
spec-quality: independent code/requirements review on the candidate.
contract-tests: real implementation against API normal, empty, and failure semantics.
product-e2e: real compatible UI/service/persistence combination on the exact manifest.

All commands and runtime results must come from the executor's real environment. Record
nonzero exits and inconclusive infrastructure outcomes honestly. Only passing required
checks on matching revision/context satisfy the product gate. No deployment authorization.
