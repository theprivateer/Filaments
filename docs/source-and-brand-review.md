# Source, licence and branding review

Evidence checked: 3 October 2026

This note records source facts and unresolved release decisions. It isn't legal advice.

## Bambu Studio data

The filament identity and colour source is the official Bambu Studio repository:

- Repository: <https://github.com/bambulab/BambuStudio>
- Pinned colour file: <https://github.com/bambulab/BambuStudio/blob/da8b44ee34dd349f2ae0df3f1cbae366df482354/resources/profiles/BBL/filament/filaments_color_codes.json>
- Repository licence: <https://github.com/bambulab/BambuStudio/blob/da8b44ee34dd349f2ae0df3f1cbae366df482354/LICENSE>

The pinned repository licence contains the GNU Affero General Public License version 3. The colour file is stored inside that repository and doesn't carry a separate file-level licence notice.

The AGPL text covers software and other copyrightable works. It says output from running a covered work is covered only when the output itself constitutes a covered work. That text alone doesn't decide whether extracting, normalising and redistributing the filament records makes the app catalogue a covered work. Qualified advice still needs to answer that question and identify any source-offer, notice or licence obligations for App Store distribution.

Before release, qualified advice must confirm the obligations that apply when the app redistributes transformed records from this file. The repository contains a small working snapshot for the six bundled proof entries and evidence-matched draft families. The complete 318-record upstream working copy remains ignored. Neither approach settles the release question.

## Australian store access

Australian product pages are the intended evidence for regional availability and packaging:

- Collection: <https://au.store.bambulab.com/collections/bambu-lab-3d-printer-filament>
- PLA Basic: <https://au.store.bambulab.com/products/pla-basic-filament>
- PLA Matte: <https://au.store.bambulab.com/products/pla-matte-filament>
- PETG HF: <https://au.store.bambulab.com/products/petg-hf>

Current official policy evidence:

- [Bambu Lab Terms of Use](https://bambulab.com/en-au/policies/terms), last updated 24 April 2024 on the page.
- [Bambu Lab Online Store Terms of Sales](https://bambulab.com/en-au/policies/page/store-tos), last updated 12 June 2026 on the page.

The Terms of Sales say they apply to users who access or browse the store and identify `https://au.store.bambulab.com/` as the Australian store. They govern ordinary store use but don't expressly grant permission for automated collection or reuse of product data. The current review also couldn't preserve an authoritative automated-access policy from the store. Silence on that point isn't approval.

Automated store access therefore remains disabled. The project accepts a manually prepared store snapshot and records its review status. Adding a fetcher requires a separately recorded terms review or written permission that covers the planned request rate, stored fields and redistribution purpose.

Sold-out status doesn't change catalogue availability. A missing page or colour also can't mark an entry discontinued. Confirmed discontinuations require a reviewed override with a reason and source.

## Branding and attribution

The official Terms of Use reserve rights in Bambu Lab's visual interfaces, graphics, design and other product elements. The current evidence check didn't find public brand guidelines authorising third-party logo or trade-dress use. The repository licence doesn't provide separate brand permission, so its software and data terms mustn't be treated as approval to use Bambu Lab marks.

The app currently uses a neutral spool icon, plain-text product names and a clear independence statement. It doesn't use the Bambu Lab logo or copy the store's visual design. In-app source and licence links now point to the exact pinned Studio revision supplied by the bundled catalogue rather than the moving `master` branch.

Before App Store submission, decide:

- The final product name and subtitle.
- Whether Bambu Lab names or marks appear in the icon, screenshots or store listing.
- The wording that explains the app is independent and isn't endorsed by Bambu Lab.
- The in-app attribution for catalogue sources and their licences.
- Whether product-page links and product names comply with applicable brand guidance.

A draft About sheet now includes the independence statement, local-data explanation, pinned source links and bundled catalogue version. Its implementation is recorded in `privacy-and-attribution.md`. No release wording has been approved yet.

## Decision record

| Topic | Current decision | Approval needed |
| --- | --- | --- |
| Studio data redistribution | Keep the full upstream document out of the committed app resources and ship only the proof catalogue until the licence review is signed. | Qualified advice on the transformed catalogue and App Store distribution obligations. |
| Australian store access | Use reviewed manual snapshots only. No store fetcher or build-time network access. | Written permission or a recorded policy review before any automated collector is added. |
| Product naming | Use factual material and colour names only where needed to identify catalogue entries. | Final App Store name, subtitle and product-description review. |
| Logo and trade dress | Use the neutral spool icon and avoid Bambu Lab logos or store styling. | Final icon, screenshots and listing review. |
| Independence wording | Keep “independent” and “isn't affiliated with or endorsed by Bambu Lab” in the About screen. | Final legal and App Store copy approval. |

## Release gate

A catalogue may replace the bundled prototype only when all of these conditions are met:

1. The Australian snapshot has `review.status` set to `approved`, with a reviewer and date.
2. Source validation passes with `--require-approved-store`.
3. The generated difference report has been reviewed.
4. All uncertain matches and missing products have a recorded decision.
5. Licence, store-access and branding decisions above have been resolved.
