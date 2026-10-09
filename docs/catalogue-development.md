# Catalogue development

The committed `Filaments/Resources/catalogue.json` file is the app's only catalogue input. App builds and launches don't fetch data from the internet.

The current file is a six-entry proof catalogue. It checks the compound identity, schema, solid and gradient swatches, alpha-bearing translucent colours, support material, packaging forms and uncertain-source states. Entries marked `reviewNeeded` or `unknown` are deliberately hidden from the default library unless the user already owns them or marks them for replacement. `catalogue/source-manifest.json` records the pinned upstream revision and proof-page sources.

Run local validation with:

```sh
python3 tools/validate_catalogue.py Filaments/Resources/catalogue.json
python3 tools/validate_catalogue_sources.py \
  --studio catalogue/snapshots/studio-prototype.json \
  --store catalogue/snapshots/au-store-prototype.json
python3 -m unittest discover -s tools/tests
```

The offline candidate generator is documented in `catalogue/README.md`. It consumes saved snapshots, reviewed compound-key mappings and overrides, then writes a candidate, difference report and source manifest. It doesn't fetch live sources.

Use `tools/prepare_studio_snapshot.py` to attach the pinned commit and retrieval date to an upstream Studio colour document. Source validation requires the full commit, and generation rejects a revision mismatch. Full upstream working copies belong in the ignored `catalogue/work` directory until the redistribution review is resolved.

Store snapshots have an explicit review state. Draft snapshots can generate review candidates. Release candidates must pass source validation with `--require-approved-store`, which also requires the reviewer and review date.

When replacing an approved catalogue, compare it with the preceding version:

```sh
python3 tools/validate_catalogue.py path/to/candidate.json --previous path/to/approved.json
```

This rejects removed keys and identity reassignment. Any future fetcher remains separate from candidate generation and Xcode builds.

## Review gates still open

- Get legal advice on redistributing data sourced from the AGPL-3.0 Bambu Studio repository.
- Review the Australian store terms before automating access.
- Confirm each prototype store-variant match and packaging form.
- Add a reviewed discontinued fixture from preserved source evidence.
- Decide app naming and trademark wording before release.
