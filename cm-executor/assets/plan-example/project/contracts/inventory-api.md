# Inventory read contract v1 — candidate, synthetic example

Owner: inventory contract owner. Consumer: UI. Provider: inventory service.
Operation: readInventory() returns Result<List<{itemId:string, quantity:int}>, Unavailable>.
IDs are unique opaque nonempty strings. Quantity is nonnegative. Order is ascending itemId
by ordinal comparison. Reading has no side effects; quantity totals must not change.
An empty list is a valid inventory. A backend failure is Unavailable, not an empty list.
A read captures one consistent repository snapshot; mixtures of concurrent snapshots are
not permitted. Local UI fixtures include two items, empty inventory, and Unavailable.

Boundary reviews verify these semantics and agreement with INV-READ and UI-LIST. This
file is a candidate until an independent contract-review check establishes its gate.
No planner-issued runtime attestation is transferred with this file. Breaking changes
return as a CM_REPLAN_REQUEST.json to the separate CM_Planner session.
