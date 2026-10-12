# Filaments

Filaments is an iPhone app for browsing Bambu Lab filament colours sold in Australia and keeping a simple local inventory. You can mark each filament as owned on a spool, owned as an unmounted refill, or needing replacement. Search and filters help narrow the catalogue, and the Inventory view counts the spools and refills in the current results.

The app stores selections on the device. Its catalogue ships with the app, so browsing and inventory tracking work without an account or internet connection. Filaments is independent and isn't affiliated with or endorsed by Bambu Lab.

## Build

Open `Filaments.xcodeproj` in Xcode, select the **Filaments** scheme and an iPhone simulator, then run the app. The minimum deployment target is iOS 17. For a physical device, select a signing team that can use `au.com.truenorthlabs.Filaments`.

## Project status

The bundled 274-entry Australian catalogue is a review draft, not a release-approved list. Catalogue matching, availability decisions, source licensing and branding still need sign-off before public distribution. See [manual build notes](docs/manual-review-build.md), [project progress](PROGRESS.md) and [source and branding review](docs/source-and-brand-review.md) for details.

## Licence

The original app and tooling code, and project documentation, are available under the [MIT License](LICENSE). MIT permits commercial reuse. This licence doesn't cover the bundled filament catalogue, source snapshots or other third-party data, and it doesn't grant rights to Bambu Lab names or trademarks. The rights and obligations for sharing the catalogue remain under review in the [source and branding notes](docs/source-and-brand-review.md).
