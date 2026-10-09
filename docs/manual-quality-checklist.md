# Manual quality checklist

Last updated: 3 October 2026

Use this checklist on the release candidate after the bundled catalogue has been approved. Record the device, OS version, app build and tester beside the completed run. A simulator run is useful, but it doesn't replace checks on physical iPhone and iPad hardware.

## VoiceOver

Run the following on one supported iPhone and one supported iPad with VoiceOver enabled.

- Open the library and move through the About button, All, Inventory and Replace scopes, search field, Filters button and several filament rows. Confirm focus order follows the visual order.
- Confirm each filament row announces its colour name, material variant, swatch description and every applicable state, including spool, refill, needs replacement and discontinued.
- Open solid, gradient, translucent and multicolour entries. Confirm the large swatch has a useful description and isn't announced only as an image or colour value.
- Change the spool, refill and replacement switches independently. Confirm each switch announces its label, current value and changed value.
- Open Filters, select more than one material family or variant, apply spool and refill filters, clear the filters, and confirm every control has an understandable label and value.
- Select Inventory with no owned entries and perform a search with no matches. Confirm the empty-state title and recovery guidance are both announced.
- Open a discontinued owned item. Confirm the discontinued explanation is announced, inventory remains editable and no purchase link is offered.
- Open About. Confirm the local-storage statement, catalogue behaviour, independence statement, source links, catalogue version and entry count are reachable and understandable.
- Activate each available link and confirm VoiceOver makes clear that it opens external Bambu Lab or source material.
- Confirm there are no focus traps, unexpected focus jumps, duplicate announcements or controls that require sight to understand.

## Display and interaction

- Repeat the primary inventory flow in light and dark appearance.
- Repeat it at the smallest and largest supported Dynamic Type sizes in portrait and landscape.
- Confirm pale and white swatches retain a visible border, and dark swatches remain distinct from their background.
- Confirm gradient and multicolour swatches preserve their colour order without clipping.
- Confirm every control remains reachable with Switch Control or Full Keyboard Access where available.
- Confirm sheets can be dismissed without losing changes that were explicitly saved.

## Persistence and upgrade

- On a clean installation, confirm the approved catalogue imports and the About sheet reports its expected version and entry count.
- Mark separate entries as spool only, refill only, both, replacement only and owned plus replacement. Force-quit and relaunch, then confirm every state survives.
- Install the release candidate over a build containing the previous approved catalogue. Confirm renamed entries and changed swatches update while all inventory flags remain unchanged.
- Confirm a removed source entry remains locally available as a review-needed record rather than disappearing.
- Confirm an owned discontinued entry remains in Inventory and an unowned replacement-marked discontinued entry remains in Replace.
- Simulate or install a build with malformed or unsupported bundled catalogue data. Confirm the last successfully imported catalogue and all inventory data remain usable.

## Sign-off record

Record a dated result for each device class. Any failure blocks release until it is fixed or accepted with a written reason.

| Device | OS | Build | Tester | VoiceOver | Display and interaction | Persistence and upgrade | Date |
| --- | --- | --- | --- | --- | --- | --- | --- |
| iPhone |  |  |  |  |  |  |  |
| iPad |  |  |  |  |  |  |  |
