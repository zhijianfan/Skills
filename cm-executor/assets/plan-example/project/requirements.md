# Requirement snapshot — synthetic example

- INV-READ: Given stored inventory entries, return each item ID and its integer quantity
  without modifying inventory. Quantities are nonnegative; empty inventory returns [].
  Unknown item IDs are opaque strings, not errors. A repository failure is an explicit
  unavailable error, never an empty successful result.
- UI-LIST: Render every returned entry with its quantity; render a visible empty state
  for []; render an error state on unavailable. UI uses the published API, not persistence.

Acceptance: actual UI, service, and persistence fixture are integrated and checked for
normal, empty, and unavailable cases on one identified combined revision. A mocked
API is permitted for local UI development but not the final product gate.

Non-goals: item transfer, authentication, purchases, and deployment. Example source
code is not included and no tests are claimed to have run.
