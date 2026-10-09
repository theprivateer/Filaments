# Manual Xcode review build

The app target currently bundles the 274-entry Australian catalogue draft, version `2026.10.02.2`. This is a review build. The source snapshot and colour mappings haven't received final human sign-off. Of the 274 entries, 266 are marked active and eight are marked `reviewNeeded`.

Open `Filaments.xcodeproj` in Xcode, choose the `Filaments` scheme and an iPhone simulator, then select **Product > Run**. The project has an iOS 17 minimum deployment target and also supports iPad. For a physical device, select your signing team and ensure the app's bundle identifier is registered to that team in Signing & Capabilities before running.

For the App Store Connect record, use **Filaments - Inventory Tracker** as the app name. Keep the Xcode target and Home Screen display name as **Filaments**, with bundle identifier `au.com.truenorthlabs.Filaments`. The App Store name is entered in App Store Connect; it isn't set by the Xcode project.

The eight uncertain entries are hidden by default. Open **Filters > Include entries needing review** to inspect them. Their rows have a “Review needed” badge, and their detail sheets show the current status. The **About** sheet should report version `2026.10.02.2` and 274 entries. The Inventory view shows spool and refill totals for the currently visible entries, updating as search and filters change.

The renamed target has a new bundle identifier. Inventory in an earlier test installation stays in that installation's local store and won't appear in Filaments. Future builds using the Filaments identifier will import catalogue updates while preserving selections by compound key. Removing an installation also removes its local inventory.

The bundled JSON is byte-for-byte identical to `catalogue/candidates/2026.10.02.2-draft.json`. The former six-entry proof bundle is preserved as `catalogue/snapshots/proof-catalogue.json`, and the candidate source manifest points to that preserved predecessor. The app build uses only local files and needs no network access.

This build is for manual review. Catalogue sign-off, the eight availability decisions, source and branding review, and device checks are still required before a release catalogue can be frozen.
