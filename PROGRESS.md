# Filaments progress

Last updated: 9 October 2026

The broader release goal is paused while the current app is prepared for manual Xcode review. The app target now bundles the full 274-entry draft. See `docs/manual-review-build.md` for build and review instructions; this draft remains unapproved.

The app, Xcode project, scheme, targets, test bundles, identifiers, About copy and documentation have been renamed to Filaments. The containing repository directory keeps its existing name. The new bundle identifier creates a separate local app store from earlier test installations.

Status meanings: `Complete` has implementation and verification evidence. `In progress` has working code but hasn't met the stage exit condition. `Pending` hasn't started.

## Current position

| Stage | Status | Summary |
| --- | --- | --- |
| 1. Catalogue proof | In progress | Compound identity, a pinned Studio revision, schema and varied swatches are represented. Store-match approval, legal review and a confirmed discontinued record remain open. |
| 2. Full catalogue pipeline | In progress | The offline generator validates saved sources, records draft or approved AU review state, retains prior entries, and writes candidates, reports and manifests. Complete Australian snapshots and review are still missing. |
| 3. App foundation | Complete | SwiftData models, bundled import, non-destructive reconciliation and upgrade fixtures are implemented and tested. |
| 4. Inventory interface | Complete | Library, search, primary scopes, detail editing, multi-select material filters, packaging filters and discontinued/historic treatment are implemented. UI tests cover the agreed inventory paths, filtered spool/refill totals, save-failure handling, varied swatches, light and dark appearance, layouts, empty states, upgrade behaviour and core accessibility audit, including an owned discontinued item whose replacement state remains editable. |
| 5. Quality pass | In progress | VoiceOver descriptions, large-text row layout, automated accessibility audits and local-data/source disclosure are implemented. Compact-iPhone and iPad audits, large text, landscape, explicit dark appearance and varied-swatch checks pass. The 274-entry draft meets the import, update and filtering budgets. A manual VoiceOver check remains. |
| 6. Release process | In progress | Offline release-readiness checks, clean-install and multi-version upgrade UI coverage, and manual sign-off checklists are in place. No release catalogue has been frozen or approved. |

## Completed work

### Catalogue and build

- Defined schema version 1 with document metadata and typed entries.
- Adopted `profileId:colourVariantId` as the stable key.
- Added a six-entry proof catalogue covering solid, gradient and translucent swatches, several material families, support material, and multiple packaging forms.
- Preserved the six-entry proof catalogue as `catalogue/snapshots/proof-catalogue.json` and copied the exact 274-entry draft into the app bundle for manual Xcode review. A library notice identifies the draft, and Filters can show all eight entries needing review.
- Added Swift and Python validation for duplicate keys, identity mismatches, invalid colours, swatch cardinality, required fields, region, entry count, schema version and active Australian evidence.
- Tightened both validators around catalogue metadata shapes. Malformed or non-string keys now produce a clear validation failure instead of crashing the offline build check; blank alternate names and invalid `lastSeenActive` dates are rejected before reconciliation, and the offline validator also checks the optional evidence note type.
- Extended both validators to check the full document header, pinned Studio revision, source retrieval dates, optional checksum format, fixed manufacturer, short colour code, first-seen version, source path and Australian store URL origin.
- Made the app validator require ASCII hexadecimal colour values, matching the canonical JSON validator, and added native rejection tests for malformed metadata and untrusted store URL origins.
- Added a native forward-compatibility test confirming that unknown document, entry and evidence fields decode harmlessly.
- Added previous-catalogue checks for removals and identity reassignment.
- Added an offline Xcode validation phase before compilation.
- Extended the build validation phase with a local-only runtime policy check. Runtime networking clients and frameworks fail the build, while external SwiftUI links that open in the system browser remain allowed.
- Confirmed `catalogue.json` is copied into the application bundle.
- Pinned the proof data source to Bambu Studio commit `da8b44ee34dd349f2ae0df3f1cbae366df482354`.
- Added an offline candidate generator that writes canonical JSON, a difference report and an input-checksum manifest.
- Added reviewed override enforcement, unmatched-variant reporting, prior-entry retention and reactivation reporting.
- Added strict offline validation for Studio records and normalised Australian store snapshots.
- Required each Studio snapshot to record its pinned 40-character commit and the SHA-256 of the exact upstream document. Generation rejects a revision mismatch.
- Added a deterministic Studio snapshot preparation tool and kept unreviewed full upstream data in the ignored `catalogue/work` area.
- Prepared and validated the pinned full Studio document locally: 318 colour records across 46 material types. The existing draft AU mappings generate against it with zero unmatched variants.
- Added an approval guard that prevents a draft store snapshot from being used for a release operation.
- Added committed source snapshots and generated a reproducible draft candidate, review report and checksum manifest.
- Corrected Studio swatch classification for the pinned `多拼色` source value. The regenerated draft now contains 230 solid, 24 translucent, 13 gradient and seven multicolour entries; regression tests cover gradient, multicolour and alpha-based translucent inference.
- Expanded the draft Australian snapshot from three to five products using official AU pages for PETG Translucent and Support for PLA/PETG. The regenerated report records both changes while keeping the snapshot unapproved.
- Added all seven PLA-CF compound-key mappings after the official AU page confirmed spool and refill packaging and its linked Bambu Lab colour table exactly matched the pinned Studio names and swatches. The mappings remain draft pending reviewer approval.
- Added all four PLA Galaxy compound-key mappings after the official AU page confirmed spool-only packaging and its linked Bambu Lab colour table exactly matched the pinned Studio names and swatches. These mappings also remain draft.
- Added all five PLA Glow and both PLA Marble compound-key mappings. Their official AU pages confirm spool-only packaging, and the linked Bambu Lab colour tables exactly match the pinned Studio records. These mappings remain draft.
- Added all five PLA Metal compound-key mappings after its official AU page confirmed spool-only packaging and the linked Bambu Lab colour table exactly matched the pinned Studio records. These mappings remain draft.
- Added all six PLA Sparkle and all six PLA Wood compound-key mappings. Their official AU pages confirm spool-only packaging, and their linked Bambu Lab colour tables exactly match the pinned Studio records. These mappings remain draft.
- Added all thirteen PLA Silk+ compound-key mappings. The official AU page exposes spool packaging and its linked Bambu Lab colour table exactly matches the pinned Studio records. General refill instructions aren't treated as proof that refills are currently offered. These mappings remain draft.
- Added all ten PLA Translucent compound-key mappings. The official AU page exposes spool packaging, and its linked Bambu Lab colour table matches every Studio name and RGB value. The Studio alpha channel remains authoritative for the translucent swatches. These mappings remain draft.
- Added all five PLA Pure and all eight PETG Matte compound-key mappings. Both official AU pages offer refills and filament with spool, and their linked Bambu Lab colour tables match the pinned Studio swatches. PLA Pure retains Studio's corrected “Absolute Black” name rather than the table's “Absolute Balck” typo. These mappings remain draft.
- Added thirteen current PETG Basic compound-key mappings with refill and spool packaging. The official AU page and colour table omit four additional Studio identities, so Purple, Sunflower Yellow, Bright Green and Hot Pink remain unmapped and aren't treated as discontinued. The mappings remain draft.
- Added twelve current ABS mappings with refill and spool packaging. Beige, Yellow, Mint and Lavender remain Studio-only review candidates because the current AU colour table omits them; they aren't treated as discontinued.
- Added all six ASA mappings with spool packaging and all seven PLA Tough+ mappings with refill and spool packaging. Their live official AU pages and Bambu Lab colour tables match the pinned Studio names and swatches. These mappings remain draft.
- Added all six PETG-CF mappings with refill and spool packaging, plus all three PC FR mappings with spool packaging. Their live official AU pages and linked Bambu Lab colour tables match the pinned Studio names and swatches. These mappings remain draft.
- Expanded PETG HF to all fourteen current AU colours and PETG Translucent to its eight current AU colours. PETG HF Red remains `reviewNeeded` because the AU table and pinned Studio swatches disagree. PETG Translucent Clear remains unmapped because it isn't in the current AU evidence; neither case is treated as a discontinuation.
- Added PVA Clear as a spool-only support material from the live official AU page and colour-table evidence. The mapping remains draft.
- Expanded PLA Basic to all thirty current solid colours with refill and spool packaging. Its eight Studio gradient identities remain unmapped review candidates. The retail spelling “Blue Grey” is retained as an alternate name for Studio's “Blue Gray”.
- Expanded PLA Matte to all twenty-five Studio colours with refill and spool packaging after visually inspecting the linked Bambu Lab colour table. Every name and swatch matches. These mappings remain draft.
- Added active spool-only Support for PLA and Support for ABS entries using the exact colour identifiers exposed by their live AU pages.
- Added Support for PA/PET as `reviewNeeded`. Its live official page exposes Green (65500), shows a sold-out purchase state and explicitly says the product has been discontinued. Human approval is still required before assigning `discontinued`.
- Added six single-colour, spool-only engineering materials whose live official pages expose exact Studio identities: PAHT-CF, PA6-CF, PET-CF, PPA-CF, PPS-CF and ASA Aero. These mappings remain draft.
- Added all eight ABS-GF and all eight PA6-GF identities from their live official AU pages. ABS-GF Green and Yellow, plus PA6-GF Yellow, Lime and Brown, remain `reviewNeeded` because the pages explicitly say they have been discontinued. Human approval is still required before assigning `discontinued`.
- Added ASA-CF Black as `reviewNeeded`. The live official AU page says the current 1 kg variant is discontinued and that a replacement size will follow, so the app catalogue treatment needs human review.
- Added all five TPU 85A, all eight TPU 90A, all six TPU 95A HF and all seven TPU for AMS identities. The live official AU pages expose the exact five-digit identifiers and packaging forms. TPU for AMS offers refill and spool; the other three products are spool-only.
- Enumerated all five pages of the live Australian filament collection. Added every previously missing material page that exposed current identities: all eight PLA Basic Gradient colours, ten PLA Silk Multi-Color colours, all four PC colours, and PLA Aero White and Gray. PLA Aero Black remains a Studio-only review candidate because it isn't present in the current AU page data.
- Added Support for PLA/PETG Black after the current live page exposed it alongside Nature. PLA Basic Arctic Whisper now has direct Australian evidence through the PLA Basic Gradient page and no longer needs `reviewNeeded` treatment.
- Added a dated Australian collection audit that accounts for all 52 listing cards: 42 distinct material pages are mapped, while ten bundles and accessories are excluded with reasons. The audit remains draft pending human review.
- Extended the Studio-to-AU coverage report to name Studio-only identities inside partially mapped material types. This exposes review gaps without treating fully unmapped Studio families, or any individual identity, as evidence of Australian sale or discontinuation.
- Changed candidate generation so every explicitly `reviewNeeded` store mapping appears in the human-readable warnings section. PETG HF Red's swatch disagreement is now called out directly in the draft review report.
- Recorded the source, licence, store-access and branding release gates in `docs/source-and-brand-review.md`.
- Added an offline release-readiness checker that blocks draft store reviews, unresolved availability, mismatched source metadata or input/output hashes, incomplete review reports, and non-release catalogue versions.
- Added a guarded catalogue-freeze tool that enforces a newer `YYYY.MM.DD.N` version, archives the exact approved inputs and review artefacts, refuses duplicate releases, and atomically promotes the canonical JSON into the app bundle.
- Added a deterministic per-product and per-colour AU review checklist tied to the Studio snapshot, reviewable store content and collection-audit hashes. Completion requires every packaging form and colour mapping to be approved and all uncertain availability to be resolved. The approval command then writes immutable sign-off hashes into a separate approved store snapshot.

### Persistence

- Added separate `FilamentCatalogueRecord` and `InventoryState` SwiftData models.
- Reconciliation inserts and updates catalogue rows by stable key.
- Missing rows aren't deleted. They are retained and marked `reviewNeeded` internally.
- Inventory flags are stored separately and aren't touched during catalogue import.
- Failed catalogue loading leaves the existing store available and shows an in-app warning.
- Added a forced catalogue-save failure test at the real reconciliation save boundary. It proves rollback restores updated catalogue fields, removes unsaved inserts, restores missing-row presence and availability, preserves inventory, and leaves the successfully imported version unchanged.
- Empty inventory records aren't created merely by opening a detail sheet.
- Inventory edits now remain in a local draft until Done is selected. A successful SwiftData transaction dismisses the sheet, while a failed save rolls back, keeps the sheet open and shows the error. Native tests force both insert and update failures and prove the stored state is restored.
- Added a Debug-only failed-save fixture and end-to-end UI test. It verifies the alert copy, keeps the unsaved draft visible for retry, and proves after relaunch that the failed edit never reached persistent storage. Release builds exclude the fixture and its simulated error.
- Empty and unchanged drafts don't write inventory rows or alter `lastModified`; native tests exercise inserts and updates through the real in-memory SwiftData context.

### Interface

- Added All, Inventory and Replace scopes.
- Added search across names, material fields and Bambu identifiers.
- Added solid, gradient and translucent swatches with visible borders.
- Added spool, refill, replacement and discontinued labels.
- Added independent spool, refill and replacement toggles.
- Added an active-product link and discontinued explanation.
- Configured an iOS 17 minimum target for iPhone and iPad.
- Added multi-select material-family and material-variant filters.
- Added spool, refill, discontinued and historic filters.
- Added an explicit native filter matrix for spool-only, refill-only, both packaging forms, replacement within a material family, search combined with ownership, and tracked uncertain entries.
- Added a UI test target with deterministic local-store reset support.
- Added UI tests for spool persistence, replacement without ownership, combined material and ownership filters, clearing material-variant filters, and owned discontinued-item treatment.
- Added a UI test for the inventory save-error path, including draft retention and post-relaunch rollback verification.
- Added explicit, accessible empty states for an empty inventory and unmatched searches. Both expose recovery guidance and have end-to-end UI coverage.
- Added an end-to-end installed-catalogue upgrade fixture. It starts several catalogue versions behind, confirms bundled fields update, preserves every inventory flag and retains an owned entry missing from the new bundle as `reviewNeeded`.
- Added a Debug-only UI fixture that marks a proof entry discontinued and seeds ownership plus replacement state. Release builds don't recognise the destructive test launch arguments.
- Added explicit VoiceOver row labels and hints that include the colour name, material, swatch type and inventory states.
- Changed status badges to stack at accessibility text sizes instead of competing for horizontal space.
- Added a largest-accessibility-text UI check using Xcode's Dynamic Type and clipped-text audit.
- Added a full Xcode accessibility audit for the main library and filament detail screens. It found and prompted fixes for low-contrast secondary labels and the detail explanation.
- Added a repeatable dark-appearance accessibility test. A Debug-only SwiftUI fixture forces dark rendering, and the test asserts the actual colour scheme before auditing the library and detail screens.
- Added end-to-end swatch-description coverage for gradient, translucent and multicolour rows and large detail swatches. The multicolour fixture exists only in Debug builds.
- Limited audit exceptions to known system-rendered SwiftUI Form labels and un-attributed iPad modal findings. App-controlled elements aren't excluded.
- Added an About sheet that explains local-only storage, bundled catalogue behaviour, independence from Bambu Lab, catalogue sources and the bundled catalogue version.
- Pinned the About sheet's Studio data and licence links to the exact revision recorded in the decoded catalogue, with a safe repository fallback for an invalid revision.
- Added stable accessibility identifiers for the About source links and made its UI test scroll through off-screen disclosures on compact devices.
- Shortened the search prompt to prevent clipping at the largest accessibility text size on iPad.
- Added a repeatable landscape clipped-text audit and made toggle assertions wait for accessibility values to settle between UI-test interactions.
- Added the 274-entry draft as a unit-test resource and exercised it through the production decoder, validator, SwiftData reconciler and library filter. The same JSON is now bundled by the app target for manual review.
- Added performance guardrails of five seconds each for first import and catalogue update, plus one second for 250 combined search/filter passes over all 274 records.
- Added a neutral 1024 px app icon showing a three-colour filament spool. It contains no text, Bambu Lab logo or branded trade dress, and remains subject to the final naming and trademark review.
- Enabled the `AppIcon` set for Debug and Release. The built app contains the expected iPhone and iPad icon metadata and an empty generated `UILaunchScreen` dictionary.
- Recorded the matching privacy and attribution release checks in `docs/privacy-and-attribution.md`.
- Rechecked the official Studio licence, Terms of Use and current Terms of Sales, and recorded the factual findings plus explicit licence, store-access and branding decisions that still require approval.
- Added a repeatable manual release-candidate checklist for VoiceOver, display modes, physical-device interaction, persistence and catalogue upgrades.
- Added a first-release acceptance matrix that links every product criterion to repeatable evidence and names the remaining human release gate without treating draft catalogue coverage as approval.
- Added a privacy manifest declaring no tracking or collected data and the `CA92.1` app-only reason for the catalogue version stored in `UserDefaults`.
- Verified a Release configuration build contains the catalogue and privacy manifest while excluding the Debug-only UI-test launch arguments.

## Verification evidence

| Check | Latest result |
| --- | --- |
| `python3 tools/validate_catalogue.py Filaments/Resources/catalogue.json --previous catalogue/snapshots/proof-catalogue.json` | Passed, 274 entries |
| `python3 -m unittest discover -s tools/tests -v` | Passed, 52 tests |
| Prototype source snapshot validation | Passed, 274 Studio records and 43 AU product records; review status remains draft |
| Draft candidate generation and previous-catalogue validation | Passed, 274 entries and no unmatched variants; 268 draft additions have direct AU evidence, eight entries remain `reviewNeeded`, and swatch types now resolve to 230 solid, 24 translucent, 13 gradient and seven multicolour records |
| Full pinned Studio working snapshot | Prepared and validated 318 records across 46 material types; generated against the draft AU mappings with zero unmatched variants |
| Studio-to-AU coverage report | 43 AU product records and 274 colour mappings recorded separately from the 318 possible Studio identities; partially mapped types list their Studio-only review candidates, and review status remains draft |
| Australian collection audit | All 52 cards across five live collection pages accounted for: 42 distinct material pages mapped and ten bundle or accessory cards excluded |
| PETG Matte colour-table inspection | Official one-page PDF extracted and rendered; all eight names and hex values match Studio |
| PLA Matte colour-table inspection | Official one-page PDF rendered and visually checked; all twenty-five names and hex values match Studio |
| Release approval guard | Passed by rejecting the draft AU snapshot |
| Release-readiness checker | Unit-tested against an approved fixture and confirmed to verify the human sign-off and collection audit while blocking draft review state, unresolved or unsupported active entries, changed inputs and incomplete reports |
| Catalogue release freezer | Unit-tested to archive exact artefacts, including the sign-off and collection audit, update the bundle only from its current predecessor, and refuse duplicate release directories |
| AU per-entry sign-off | Generated a structurally valid checklist covering all 43 products and 274 mappings; approval correctly writes nothing while decisions are pending, eight statuses are unresolved, reviewer details are absent and the collection audit is draft |
| Native `FilamentsTests` suite | Passed, 28 tests on iPhone 17 Pro simulator, including pinned source-link, strict metadata, unknown-field compatibility, the agreed filter matrix, transactional catalogue and inventory persistence, and forced-save rollback |
| Focused native catalogue validation and reconciliation | Passed, 19 tests on iPhone 17 Pro, including blank alternate-name and invalid last-active-date rejection plus full rollback after a forced catalogue save failure |
| Native `FilamentsUITests` coverage | Fourteen paths verified: the original 11-test suite passed on compact iPhone 17e, and the added save-failure, varied-swatch and explicit dark-appearance paths passed on iPhone 17 Pro. Coverage includes upgrade retention, empty-state recovery guidance, About, accessibility audits, largest text, landscape and transactional save failure. |
| Post-change inventory UI rerun | Passed: Done-save and relaunch persistence, replacement without ownership, combined material and refill filtering, discontinued-item editing, and the failed-save alert, draft retention and post-relaunch rollback path all completed successfully. |
| Installed catalogue upgrade UI path | Passed from a synthetic 2024 catalogue to the current bundle; catalogue-controlled fields changed, all inventory flags survived, and an owned missing record was retained as `reviewNeeded` |
| Core-screen accessibility audit | Passed on compact iPhone 17e and iPad (A16) for the library and filament detail screens |
| Dark-appearance accessibility audit | Passed on iPhone 17 Pro after asserting SwiftUI's actual colour scheme; the library and filament detail screens then passed the same accessibility audit |
| Varied-swatch UI path | Passed on iPhone 17 Pro for gradient, translucent and multicolour row descriptions and large detail-swatch descriptions |
| Largest Dynamic Type UI test and accessibility audit | Passed on compact iPhone 17e and iPad (A16) simulators; no clipped-text or Dynamic Type audit findings, including the detail screen's clipped-text check |
| Landscape clipped-text audit | Passed on compact iPhone 17e and iPad (A16) simulators |
| Dark appearance visual check | Passed on compact iPhone 17e and iPad (A16); text, controls and pale/dark swatch borders remained legible |
| Full-catalogue performance guardrail | Passed with the regenerated 274-entry draft: native decoding confirms 230 solid, 24 translucent, 13 gradient and seven multicolour records; first import took 0.122 s, full update 0.130 s, and 250 combined search/filter passes 0.772 s; inventory state survived the update |
| Source, licence and branding evidence check | Official pinned Studio licence, Terms of Use and Terms of Sales rechecked on 3 October 2026; findings are recorded, while legal and final brand approval remain open |
| Debug build for generic iOS Simulator | Passed with catalogue and local-only runtime policy validation |
| Manual review build, 9 October 2026 | Passed for generic iOS Simulator. The built `.app` contains the exact 274-entry draft JSON; its SHA-256 matches the candidate manifest. The review filter compiles. The draft notice has since been removed from the library. |
| Inventory totals, 9 October 2026 | The Inventory view counts spool and refill selections among visible entries. Focused filter unit tests and UI tests for filtered/search totals and the removed draft notice pass on iPhone 17 Pro. |
| Focused manual-review UI smoke tests | Incomplete: Xcode's UI runner stalled before either test executed. The test process was stopped after the simulator remained booted with no final result bundle. Manual Xcode review remains the next check. |
| Bundled privacy manifest | Valid property list at the app bundle root; no tracking or collected data, with `UserDefaults` reason `CA92.1` |
| Generic Release simulator build | Passed with catalogue and local-only runtime policy validation; bundled catalogue and privacy manifest are present, and all Debug-only UI-test arguments, fixture records, appearance probes and simulated failure copy remain absent from the binary |
| Debug simulator asset build | Passed; `AppIcon` compiled for iPhone and iPad, and generated launch-screen metadata is present |
| Xcode validation phase | Passed during build |
| Local-only runtime policy | Passed across the app target and enforced during every Debug and Release build; URLSession, Network.framework and embedded web clients are rejected |
| Bundled `catalogue.json` presence | Exact copy of the 274-entry draft, with the six-entry predecessor preserved separately |
| `git diff --check` | Passed |
| Main library visual check | Passed on iPhone 17 simulator; compact navigation layout corrected |

## Next implementation slice

1. Have a human reviewer complete `catalogue/reviews/2026.10.02-au-store-signoff.json`, then resolve the eight `reviewNeeded` entries and regenerate the checklist against the corrected snapshot.
2. Preserve a reviewed collection-level audit that accounts for bundles, trial packs, accessories and every listed material page before approving the snapshot.
3. Confirm whether the Studio-only identities in partially mapped families are old, future or regional variants. Absence alone mustn't change their status.
4. Add a reviewed discontinued catalogue record backed by preserved evidence; the UI behaviour is already covered by a Debug-only end-to-end fixture.
5. Complete and sign off `docs/manual-quality-checklist.md` on a physical iPhone and iPad.

## Known development environment notes

- CoreSimulator access is blocked inside the managed command sandbox, but simulator builds and tests run normally with the required host permission.
- Xcode 27 can hang while saving an `.xcresult` after a failed UI test. The test outcome is printed first, and successful runs exit normally.
- Xcode 27's UI-test launch worker has also returned CoreSimulator Mach error `-308` and stalled while materialising workers. Restarting CoreSimulator, fully booting a simulator and allowing the slow worker start to finish recovered both native and UI tests.
- Generated launch-screen metadata is present in the built app and a clean app build succeeds. Xcode's iPad UI-test runner still emits a launch-screen warning for its runner process.

## Open review gates

- Confirm every proof catalogue store match and packaging form.
- Review Bambu Studio data redistribution under AGPL-3.0 with qualified legal advice.
- Review Australian store terms before automated fetching.
- Settle app naming, attribution and trademark wording.
- Replace the proof catalogue with an approved full Australian catalogue before release.

## Decision log

- 2 October 2026: Use compound Bambu identity keys, never colour names or hex values alone.
- 2 October 2026: Keep catalogue and inventory in separate SwiftData models.
- 2 October 2026: Treat the bundled JSON as the app's only runtime catalogue source.
- 2 October 2026: Hide uncertain catalogue states by default while preserving owned or replacement-marked items.
- 2 October 2026: Set iOS 17 as the minimum deployment target and support iPhone and iPad.
- 2 October 2026: Keep Australian store ingestion manual until the automated-access terms review is recorded.
- 2 October 2026: Require explicit approved review metadata before a store snapshot can be used for a release candidate.
- 2 October 2026: Keep full upstream Studio working copies ignored until the data redistribution review is resolved; record both the pinned commit and raw-document SHA-256.
- 3 October 2026: Generate approved AU snapshots only from a complete per-product and per-colour sign-off, then verify and archive the sign-off and collection-audit hashes during release.
