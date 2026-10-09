# Privacy and attribution

Last reviewed: 2 October 2026

## Runtime behaviour

Filaments stores catalogue records and inventory selections in the app's local SwiftData store. It has no account system, analytics, advertising SDK, remote catalogue feed or app server. Opening an Australian product page or a source link hands the URL to the system browser; the app doesn't query those sites itself.

The current implementation doesn't collect or transmit user data. App Store privacy answers should be checked again whenever dependencies or network features change.

Every app build runs the repository-owned `tools/validate_runtime_policy.py` script over the app target. The target allows this trusted script to read the source tree rather than relying on Xcode's per-input script sandbox. The check rejects runtime networking frameworks and clients while allowing SwiftUI links that hand approved URLs to the system browser. Any future remote catalogue, account, analytics or synchronisation work must deliberately update this policy and the privacy review rather than silently adding network access.

`PrivacyInfo.xcprivacy` declares no tracking and no collected data. It declares `CA92.1` for `UserDefaults`, which stores the successfully imported catalogue version inside this app only. [Apple requires apps that call a required-reason API to describe that use](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api) in the bundled privacy manifest, and lists `CA92.1` for app-only defaults.

## In-app disclosure

The About sheet tells users that:

- inventory remains on their device;
- the catalogue ships with the app;
- live listings and stock aren't fetched;
- Filaments is independent and isn't affiliated with or endorsed by Bambu Lab;
- catalogue identifiers and colour data come from Bambu Studio;
- Australian availability is reviewed against the Bambu Lab AU store.

It also shows the bundled catalogue version and entry count. Its source-data and licence links use the exact pinned Bambu Studio revision recorded in the successfully decoded bundle. An invalid or unavailable revision falls back to the repository page instead of constructing an untrusted URL.

## Release checks

Before release:

- confirm the local-only statement still matches the built binary;
- complete the Bambu Studio data redistribution review recorded in `source-and-brand-review.md`;
- approve the app name, disclaimer and product-name use;
- check App Store privacy answers against the release build;
- generate and inspect Xcode's privacy report for the archived release;
- update this document if any telemetry, remote catalogue, account or synchronisation feature is added.
