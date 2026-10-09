# Filaments implementation plan

## Product direction

Filaments uses two separate data layers: a versioned Bambu Lab catalogue and a small local record of the user's selections. This separation lets catalogue updates change names, swatches and availability without overwriting inventory.

`fila_id` identifies a filament family, such as PLA Basic, rather than a specific colour. The durable identity is therefore the compound key `fila_id:fila_color_code`. The shorter `color_code` is retained for display and cross-checking, but isn't used as the database key.

## 1. First-release scope

The first release will:

- Target iPhone, with an iPad-compatible layout where practical.
- Cover genuine first-party Bambu Lab filament sold through the Australian store.
- Include printing filament and first-party support filament.
- Treat each material-and-colour combination as one catalogue entry.
- Track three independent flags: has filament on a spool, has an unmounted refill, and needs replacement.
- Use one replacement flag for the whole filament entry, regardless of the owned packaging forms.
- Filter by all entries, inventory, replacement status, material type and discontinued status.
- Store all user data locally.
- Ship catalogue updates with app releases instead of fetching them at runtime.

The first release won't track quantities, remaining weight, purchase history, price, Bambu account data, RFID tags, third-party brands, live Australian stock or iCloud synchronisation.

“Spool” means filament currently supplied or stored on a spool. “Refill” means an unmounted refill. Spare empty reusable spools aren't part of inventory in this version.

## 2. Catalogue definition

“All available” means every distinct first-party Bambu Lab material-and-colour variant listed for sale in the Australian Bambu Lab store at the catalogue's generation date, plus historic entries retained from earlier catalogue versions.

A sold-out product remains active. Stock changes don't make a product discontinued.

Catalogue availability states:

- `active`: currently listed as a product in Australia.
- `discontinued`: manually confirmed as no longer sold.
- `reviewNeeded`: missing or ambiguous and awaiting human confirmation.
- `historical`: retained from an older catalogue but never confirmed for current sale.
- `unknown`: source information is insufficient.

Only `active` and `discontinued` need prominent treatment in the first UI. The remaining states support safe catalogue maintenance.

A product must never be marked discontinued merely because a colour is sold out, a page temporarily fails, it disappears during one source run, it's present in Bambu Studio but absent from the Australian store, or only one packaging form has disappeared. Discontinuation requires manual confirmation.

## 3. Catalogue sources

### Primary identity and colour source

Use the official Bambu Studio `filaments_color_codes.json` file for:

- `fila_id`
- `fila_color_code`
- Bambu's short `color_code`
- Filament type
- Official colour names
- Solid, gradient and multicolour swatches
- Localised names, if retained

### Australian availability source

Use the Australian Bambu Lab store to determine:

- Whether a product is sold in Australia
- Product URL
- Whether it's offered as a spool, refill or both
- Pack size or filament weight, if retained
- Whether it's printing or support material

The store isn't the primary source of stable identity. Store variant numbers and page structures may change.

### Curated overrides

Maintain a reviewed overrides file for:

- Renamed materials or colours
- Product-page aliases
- Confirmed discontinuations
- Australian-only differences
- Corrected swatches
- Excluded entries
- Manual mappings between store variants and Bambu Studio records

Each override needs a short reason and source reference.

### Source and licence review

Before release, review:

- The Bambu Studio repository licence and its effect on redistributed data.
- The Australian store's terms for automated access.
- Bambu Lab trademark and branding requirements.

The catalogue generator must identify its sources and generation date. The app mustn't imply endorsement by Bambu Lab.

## 4. Catalogue generation workflow

Catalogue generation runs outside Xcode and outside the app. App builds mustn't depend on internet access.

1. Fetch or accept a pinned snapshot of the official Bambu Studio colour file.
2. Enumerate first-party filament products from the Australian store.
3. Extract material names, colour variants, packaging forms and product URLs.
4. Normalise material names while preserving distinct variants.
5. Match Australian product variants to Bambu Studio entries.
6. Apply reviewed overrides.
7. Merge the result with the previous canonical catalogue.
8. Retain missing historic records instead of deleting them.
9. Produce a candidate catalogue and human-readable difference report.
10. Require review for additions, removals, uncertain matches and status changes.
11. Write the approved canonical JSON.
12. Run schema and consistency validation.
13. Commit the JSON, source manifest and review report together.

Matching considers the profile ID, filament type, colour variant ID, official colour name, swatch value and store product handle. A match based only on colour name or hex value can't be accepted automatically.

If an active entry disappears from a source run, preserve it, set `reviewNeeded`, keep its prior display data, and call it out in the review report. Once a discontinuation is confirmed, change only the catalogue status. The stable key stays unchanged. A discontinued entry may become active again without affecting user data.

## 5. Canonical JSON

Document metadata:

- Schema version
- Catalogue version
- Generation timestamp
- Region, fixed to `AU`
- Generator version
- Source Bambu Studio commit or release
- Source retrieval dates
- Entry count
- Optional content checksum

Entry fields:

| Field | Purpose |
| --- | --- |
| `key` | Stable compound key, such as `GFA00:10300` |
| `manufacturer` | Fixed to Bambu Lab |
| `profileId` | Original `fila_id` |
| `colourVariantId` | Original `fila_color_code` |
| `colourCode` | Bambu's shorter colour code |
| `materialFamily` | Broad filter group such as PLA, PETG, ABS or Support |
| `materialVariant` | Full type such as PLA Basic or PETG HF |
| `name` | Australian English display name |
| `alternateNames` | Previous or source-specific names |
| `swatchType` | Solid, gradient, multicolour or translucent |
| `colours` | Ordered array of RGBA hex values |
| `availability` | Active, discontinued, review needed, historical or unknown |
| `soldAs` | Spool, refill or both |
| `productURL` | Australian store product page |
| `firstSeen` | First catalogue version containing the entry |
| `lastSeenActive` | Last confirmed Australian listing |
| `sourceEvidence` | Source identifiers used during review |

Unknown extra JSON fields must decode harmlessly.

Validation fails for duplicate stable keys, missing required identifiers, invalid colours, empty solid swatches, gradients with fewer than two colours, missing material families, active entries without Australian evidence, reassigned stable keys, removed previous entries, and unsupported schema versions. Uncertain store matches and missing product URLs are warnings.

## 6. Xcode integration

The approved JSON is committed and included in the app target's resources.

The build must validate the committed JSON, fail clearly when it's missing or invalid, copy it into the bundle, and avoid all network access. Generated Swift catalogue source isn't required.

Source-fetching tools belong under `tools` or `catalogue`. Only approved canonical JSON is consumed by the app target.

## 7. Local persistence

Use SwiftUI and SwiftData with an iOS 17 minimum deployment target.

The local catalogue model stores fields needed for display and filtering, including the stable key, material classification, names, swatches, Bambu identifiers, availability, packaging forms, product URL and last imported catalogue version.

The inventory model stores only:

- Stable catalogue key
- `hasSpool`
- `hasRefill`
- `needsReplacement`
- Last modified date

Computed values:

- `isOwned = hasSpool || hasRefill`
- `isAttentionRequired = needsReplacement`
- `isUnavailableReplacement = needsReplacement && discontinued`

Replacement remains independent of ownership. No personal data belongs in catalogue records.

## 8. Non-destructive reconciliation

Run reconciliation on first launch and when the bundled version changes.

1. Decode and validate the entire bundled catalogue.
2. Find local catalogue rows by stable key.
3. Insert new records.
4. Update catalogue-controlled fields.
5. Never overwrite inventory state.
6. Never delete a local record because it's absent from new JSON.
7. Preserve absent records and flag them for review.
8. Commit only when the import succeeds.
9. Save the imported version after success.

If decoding or reconciliation fails, retain existing local data and show the previous catalogue. A catalogue error must never reset inventory.

## 9. App interaction

### Main library

Show the colour swatch, colour name, material variant, spool and refill badges, replacement indicator, and discontinued indicator. Gradient and multicolour swatches show their ordered colours.

Default sorting is material family, material variant, then colour name.

Primary scopes are All, Inventory and Replace. They are views over the same library.

### Filters

The filter sheet supports:

- One or more material families
- One or more material variants
- Has spool
- Has refill
- Discontinued
- Include historic entries

The default All view shows active products. Discontinued items still appear automatically when owned or marked for replacement.

### Search

Search colour name, material family, material variant, profile ID, colour variant ID, short colour code and alternate names.

### Detail and editing

Show a large swatch, colour and material names, Bambu identifiers, availability, three independent inventory toggles, discontinued explanation and an Australian product link for active entries.

### Accessibility

Don't represent state or colour through colour alone. Swatches need text names and accessible labels. Indicators need icons and labels. Pale swatches need borders, and multicolour swatches need useful VoiceOver descriptions.

## 10. Discontinued products

Owned discontinued items remain in Inventory with their flags intact. Users can still edit those flags. Misleading purchase actions are removed or disabled, and the app explains that the product is no longer listed in Australia.

Unowned discontinued items stay hidden unless the corresponding filter is enabled. This behaviour must survive upgrades across several catalogue versions.

## 11. Testing

Catalogue generator tests cover official records, all swatch forms, store matching, material normalisation, duplicate detection, missing fields, overrides, deterministic output, historic retention, reappearance and sold-out products remaining active. Routine tests use saved fixtures rather than live access.

Reconciliation fixtures cover first installation, additions, renames, swatch changes, discontinuation, accidental removal, reintroduction, malformed JSON, unsupported schemas and every inventory-flag combination. Catalogue updates must never alter inventory.

Filter tests cover spool-only, refill-only, both forms, replacement without ownership, material combinations, owned discontinued entries and search combined with filters.

UI tests cover inventory editing, replacement state, filters, relaunch persistence, empty states, Dynamic Type, VoiceOver labels, light and dark appearance, and varied swatches.

## 12. Delivery stages

### Stage 1: Catalogue proof

- Confirm compound identifiers.
- Build a sample across several material families.
- Verify Australian store matching.
- Resolve licensing and source-access questions.
- Agree on the canonical schema.

Exit condition: a reviewed sample handles solids, gradients, spool/refill packaging and a discontinued record.

### Stage 2: Full catalogue pipeline

- Add all official Bambu Studio entries relevant to Australia.
- Enumerate Australian products and colour variants.
- Add overrides.
- Generate the first canonical JSON and difference report.
- Review uncertain matches manually.

Exit condition: every active Australian colour variant has a stable key, material classification and swatch.

### Stage 3: App foundation

- Create the SwiftUI project.
- Add SwiftData models.
- Bundle the catalogue.
- Implement transactional import and reconciliation.
- Add migration tests.

Exit condition: catalogue updates preserve local inventory under every test fixture.

### Stage 4: Inventory interface

- Build the main library.
- Add the entry edit sheet.
- Add inventory and replacement scopes.
- Add material and ownership filters.
- Add discontinued-product treatment.

Exit condition: all agreed inventory operations can be completed without ambiguity.

### Stage 5: Quality pass

- Complete accessibility work.
- Test smaller and larger iPhones.
- Check full-catalogue performance.
- Exercise upgrade paths.
- Review copy, privacy details and product attribution.

### Stage 6: Release process

- Freeze a catalogue version.
- Save source snapshots and the review report.
- Run validation and tests.
- Perform clean-install and upgrade tests.
- Archive and distribute the build.

## 13. Ongoing maintenance

Refresh the catalogue before each planned app update, or monthly when releases are frequent.

Each refresh reports new products, new colours, changed names or swatches, packaging changes, missing products requiring review, confirmed discontinuations, reactivated products, unmatched variants and entry counts by family. A human approves the report before canonical JSON changes are accepted.

## First-release acceptance criteria

- Every currently sold Australian Bambu Lab filament colour is represented.
- Every entry has Bambu identifiers, material classification and a usable swatch.
- Users can independently mark spool, refill and replacement status.
- Inventory, replacement and material filters work together.
- Data survives termination, relaunch and catalogue upgrades.
- Source removal can't delete user inventory.
- Confirmed discontinued products remain visible to affected users.
- The app works without an account, server or internet connection.
- Catalogue generation is repeatable and produces a reviewable difference report.

