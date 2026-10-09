# Catalogue workspace

This directory holds reviewed catalogue inputs and outputs. Network fetching isn't part of an app build.

For the current Xcode review build, the app bundles the 274-entry draft. See `docs/manual-review-build.md`. The previous six-entry proof catalogue is preserved at `catalogue/snapshots/proof-catalogue.json`.

## Offline generator inputs

`tools/generate_catalogue.py` accepts four JSON inputs:

- A saved Bambu Studio `filaments_color_codes.json` snapshot with top-level `sourceRevision`, `sourceDocumentSHA256` and `retrievedAt` values beside its existing `data` array.
- A reviewed Australian store snapshot in the normalised format below.
- `overrides.json`, where every non-empty override includes `reason` and `source`.
- The previous approved canonical catalogue, when one exists.

Saved Studio and store inputs are validated before matching. Run that check directly with:

```sh
python3 tools/validate_catalogue_sources.py \
  --studio catalogue/snapshots/studio-prototype.json \
  --store catalogue/snapshots/au-store-prototype.json
```

The Studio revision must be a full lowercase Git commit. Candidate generation fails if `sourceRevision` doesn't match `--studio-revision`. Preparation records the SHA-256 of the exact downloaded document before adding local metadata.

Swatch classification follows the pinned Studio record. The source value `多拼色` maps to `multicolour`, `渐变色` records with several values map to `gradient`, and a single colour with a non-opaque alpha channel maps to `translucent`. Colour count alone can't distinguish a gradient from a multicolour filament.

Prepare the human store review checklist from the exact saved inputs and collection audit:

```sh
python3 tools/prepare_store_review.py prepare \
  --studio catalogue/snapshots/studio-prototype.json \
  --store catalogue/snapshots/au-store-prototype.json \
  --audit catalogue/reports/2026.10.02-au-collection-audit.md \
  --output catalogue/reviews/2026.10.02-au-store-signoff.json
```

The reviewer sets every product's `packagingDecision` and every colour's `mappingDecision` to `approved`, records their name and review date, and adds notes where useful. Any rejected item must first be corrected in the source snapshot. Regenerate the checklist after any source-content or collection-audit change because it records their hashes. A completed review is checked with:

```sh
python3 tools/prepare_store_review.py validate \
  --studio catalogue/snapshots/studio-prototype.json \
  --store catalogue/snapshots/au-store-prototype.json \
  --audit catalogue/reports/2026.10.02-au-collection-audit.md \
  --review catalogue/reviews/2026.10.02-au-store-signoff.json \
  --require-complete
```

Completion also requires the collection audit to say `Review status: approved` and rejects any remaining `reviewNeeded` or `unknown` store variant.

After the completed review passes, create the approved snapshot without editing its approval metadata by hand:

```sh
python3 tools/prepare_store_review.py approve \
  --studio catalogue/snapshots/studio-prototype.json \
  --store catalogue/snapshots/au-store-prototype.json \
  --audit catalogue/reports/2026.10.02-au-collection-audit.md \
  --review catalogue/reviews/2026.10.02-au-store-signoff.json \
  --output catalogue/snapshots/au-store-approved.json
```

The approved snapshot records the reviewer and date plus SHA-256 values for the sign-off and collection audit. Its reviewable store content remains identical to the signed draft.

Prepare a downloaded, pinned Studio document with:

```sh
python3 tools/prepare_studio_snapshot.py \
  --input /path/to/filaments_color_codes.json \
  --revision da8b44ee34dd349f2ae0df3f1cbae366df482354 \
  --retrieved-at 2026-10-02 \
  --output catalogue/work/studio-full.json
```

`catalogue/work` is ignored. It holds local upstream inputs while the data redistribution review remains open. A reviewed release process can copy an approved source snapshot into a committed release-snapshot location once that review is resolved.

The store document must carry a `review` object whose status is either `draft` or `approved`. An approved snapshot also needs `reviewedBy` and `reviewedAt`. Use `--require-approved-store` for a release candidate so a draft snapshot can't be accepted accidentally.

Normalised store snapshot example:

```json
{
  "region": "AU",
  "retrievedAt": "2026-10-02",
  "review": {
    "status": "draft",
    "reviewedBy": null,
    "reviewedAt": null,
    "notes": []
  },
  "products": [
    {
      "materialFamily": "PLA",
      "materialVariant": "PLA Basic",
      "productURL": "https://au.store.bambulab.com/products/pla-basic-filament",
      "soldAs": "both",
      "confirmedAt": "2026-10-02",
      "variants": [
        {
          "profileId": "GFA00",
          "colourVariantId": "10300"
        }
      ]
    }
  ]
}
```

Mappings use both Bambu identifiers. The generator reports a store variant that doesn't match the Studio snapshot instead of matching by name or colour alone. `stockStatus` may be retained as evidence, but doesn't control catalogue availability.

Run a candidate generation with saved snapshots:

```sh
python3 tools/generate_catalogue.py \
  --studio catalogue/snapshots/filaments_color_codes.json \
  --store catalogue/snapshots/au-store.json \
  --overrides catalogue/overrides.json \
  --previous Filaments/Resources/catalogue.json \
  --catalogue-version 2026.10.02.2 \
  --studio-revision da8b44ee34dd349f2ae0df3f1cbae366df482354 \
  --output catalogue/candidate.json \
  --report catalogue/reports/2026.10.02.2.md \
  --manifest catalogue/candidate-source-manifest.json
```

Review the report and candidate before replacing the bundled catalogue. Candidate generation doesn't approve uncertain matches or discontinuations.

Generate a mapping coverage report with:

```sh
python3 tools/report_catalogue_coverage.py \
  --studio catalogue/work/studio-full.json \
  --store catalogue/snapshots/au-store.json \
  --output catalogue/reports/studio-to-au-coverage.md
```

The coverage report keeps Studio record counts separate from Australian mappings. Studio presence alone isn't proof that a colour is currently sold in Australia.

Before replacing the bundled catalogue, run the release-readiness check against the approved candidate and its saved artefacts:

```sh
python3 tools/check_release_readiness.py \
  --catalogue catalogue/candidates/approved.json \
  --previous Filaments/Resources/catalogue.json \
  --studio catalogue/snapshots/studio-approved.json \
  --store catalogue/snapshots/au-store-approved.json \
  --overrides catalogue/overrides.json \
  --manifest catalogue/candidates/approved-source-manifest.json \
  --report catalogue/reports/approved.md \
  --review-signoff catalogue/reviews/approved-store-signoff.json \
  --collection-audit catalogue/reports/approved-collection-audit.md
```

The check requires an approved store review with reviewer details, the complete per-entry sign-off, matching collection-audit, input and generated-output hashes, matching source metadata, no unmatched variants or report warnings, and no `reviewNeeded` or `unknown` catalogue entries. It also reruns canonical and source validation. Passing this check confirms internal artefact consistency; legal, branding and physical-device sign-off remain separate release gates.

After every external review gate is signed off, freeze the approved artefacts and promote the catalogue with:

```sh
python3 tools/freeze_catalogue_release.py \
  --catalogue catalogue/candidates/approved.json \
  --previous Filaments/Resources/catalogue.json \
  --studio catalogue/snapshots/studio-approved.json \
  --store catalogue/snapshots/au-store-approved.json \
  --overrides catalogue/overrides.json \
  --manifest catalogue/candidates/approved-source-manifest.json \
  --report catalogue/reports/approved.md \
  --review-signoff catalogue/reviews/approved-store-signoff.json \
  --collection-audit catalogue/reports/approved-collection-audit.md \
  --bundle-target Filaments/Resources/catalogue.json \
  --releases-root catalogue/releases
```

The command reruns release readiness, refuses an old or duplicate release version, checks that `--previous` is the exact catalogue currently bundled, archives every input and review artefact under the catalogue version, then atomically replaces the bundled JSON. It won't overwrite an existing release archive. Don't run it until data redistribution, store-access, branding, catalogue and device-testing approvals are recorded.

The committed `studio-prototype.json` and `au-store-prototype.json` files exercise the workflow with the six preserved proof entries plus 268 evidence-backed draft additions. The AU snapshot contains 43 product records and 274 colour mappings. Eight candidate entries remain `reviewNeeded`: one swatch disagreement, six explicit product or colour discontinuation notices, and Support for PA/PET. The AU file is marked `draft`; it isn't evidence that the full Australian catalogue has been reviewed.
