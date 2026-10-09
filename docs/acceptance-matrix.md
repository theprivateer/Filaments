# First-release acceptance matrix

Last updated: 5 October 2026

This matrix separates implemented behaviour from release evidence that still needs human approval. `Automated` means the repository contains a repeatable check. `Human gate` means the app must not be treated as release-ready until the named review is completed.

| Acceptance criterion | Status | Evidence | Remaining release gate |
| --- | --- | --- | --- |
| Every currently sold Australian Bambu Lab filament colour is represented. | Human gate | The draft source accounts for all 52 cards across five Australian collection pages and contains 274 colour mappings across 43 product records. `catalogue/reports/2026.10.02-au-collection-audit.md` records the collection audit. | Approve every product and colour decision in `catalogue/reviews/2026.10.02-au-store-signoff.json`, resolve the eight `reviewNeeded` entries, and confirm the Studio-only identities. |
| Every entry has Bambu identifiers, material classification and a usable swatch. | Automated for the draft | `tools/validate_catalogue.py` and `tools/validate_catalogue_sources.py` reject missing identities, invalid compound keys, missing material families and invalid swatches. The 274-entry draft passes validation and production decoding. End-to-end UI checks verify useful row and detail descriptions for solid, gradient, translucent and multicolour swatches. | Human approval must establish that each mapping is the correct Australian product and colour, rather than only a structurally valid match. |
| The user can independently mark spool, refill and replacement status. | Complete | Separate fields are stored in `InventoryState`. Inventory edits commit through a tested SwiftData transaction. Forced insert and update failures prove rollback restores stored state. An end-to-end failure fixture verifies that the alert appears, the sheet retains the draft for retry, and relaunch confirms the failed edit wasn't persisted. Native and UI tests also cover independent ownership and replacement states, including replacement without current inventory and successful relaunch persistence. | Complete the physical-device checks in `docs/manual-quality-checklist.md`. |
| Inventory, replacement and material filters work together. | Complete | Production filter tests and end-to-end UI tests cover combined material, ownership and replacement paths. The full-draft performance check runs 250 combined filter passes over 274 entries. | Complete the manual release-candidate smoke test on physical devices. |
| Data survives termination, relaunch and catalogue upgrades. | Complete | UI tests cover relaunch persistence and an installed upgrade from a synthetic 2024 catalogue. Native reconciliation tests preserve every inventory-flag combination. | Run and sign off the physical-device clean-install and upgrade checks. |
| Removing a product from the source can't delete user inventory. | Complete | The reconciler retains missing catalogue rows as `reviewNeeded`. Native and installed-upgrade tests verify that an owned missing row and its inventory state survive. | None beyond the final release-candidate upgrade check. |
| Confirmed discontinued products remain visible to affected users. | Implemented, catalogue gate pending | A Debug-only end-to-end fixture verifies that an owned discontinued item remains visible and editable, including its replacement flag. | Add at least one human-confirmed discontinued record to the approved catalogue with preserved evidence. |
| The app operates without an account, server or internet connection. | Automated | The app has no account or server layer. `tools/validate_runtime_policy.py` rejects runtime networking frameworks and clients during Debug and Release builds. The bundled catalogue is the only runtime catalogue input. External product and source links open in the system browser by user action. | Complete the physical-device offline smoke test. |
| Catalogue generation is repeatable and produces a reviewable difference report. | Complete for tooling, release gate pending | The offline generator produces canonical JSON, a difference report and checksum manifest from pinned inputs. Tooling tests cover deterministic output, retained history, approval checks, readiness checks and atomic release freezing. | Complete the source, licence, store-access, branding and per-entry reviews before approving and freezing a release catalogue. |

## Release decision

The application implementation satisfies the automated parts of the first-release criteria. The app now bundles the full Australian draft for manual review, but that catalogue isn't approved for release.

Release approval requires all of the following:

1. Complete `catalogue/reviews/2026.10.02-au-store-signoff.json` and resolve every uncertain status.
2. Mark the collection audit as reviewed and preserve its approved hash.
3. Record the source, licence, store-access, naming and trademark decisions in `docs/source-and-brand-review.md`.
4. Generate the approved Australian snapshot, run the release-readiness checker, and freeze a new catalogue version.
5. Complete and sign `docs/manual-quality-checklist.md` on the release build and physical devices.

The release-freeze command is deliberately expected to fail until those gates are satisfied.
