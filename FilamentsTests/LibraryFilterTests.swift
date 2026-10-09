import Foundation
import XCTest
@testable import Filaments

@MainActor
final class LibraryFilterTests: XCTestCase {
    func testDefaultShowsActiveAndOwnedDiscontinuedEntries() {
        let filter = LibraryFilter()
        let active = makeRecord()
        let discontinued = makeRecord(availability: .discontinued)

        XCTAssertTrue(filter.matches(active, inventory: nil))
        XCTAssertFalse(filter.matches(discontinued, inventory: nil))
        XCTAssertTrue(
            filter.matches(
                discontinued,
                inventory: InventoryState(catalogueKey: discontinued.key, hasRefill: true)
            )
        )
    }

    func testInventoryAndReplacementScopesRemainIndependent() {
        let record = makeRecord()
        let replacementOnly = InventoryState(catalogueKey: record.key, needsReplacement: true)

        var filter = LibraryFilter(scope: .inventory)
        XCTAssertFalse(filter.matches(record, inventory: replacementOnly))

        filter.scope = .replace
        XCTAssertTrue(filter.matches(record, inventory: replacementOnly))
    }

    func testMultipleMaterialSelectionsCombineWithSearch() {
        let pla = makeRecord(family: "PLA", variant: "PLA Basic", name: "Orange")
        let petg = makeRecord(family: "PETG", variant: "PETG HF", name: "Orange")
        let abs = makeRecord(family: "ABS", variant: "ABS", name: "Black")

        var filter = LibraryFilter(
            searchText: "orange",
            materialFamilies: ["PLA", "PETG"]
        )
        XCTAssertTrue(filter.matches(pla, inventory: nil))
        XCTAssertTrue(filter.matches(petg, inventory: nil))
        XCTAssertFalse(filter.matches(abs, inventory: nil))

        filter.materialVariants = ["PETG HF"]
        XCTAssertFalse(filter.matches(pla, inventory: nil))
        XCTAssertTrue(filter.matches(petg, inventory: nil))
    }

    func testSpoolAndRefillFiltersRequireBothWhenCombined() {
        let record = makeRecord()
        let filter = LibraryFilter(requiresSpool: true, requiresRefill: true)

        XCTAssertFalse(
            filter.matches(
                record,
                inventory: InventoryState(catalogueKey: record.key, hasSpool: true)
            )
        )
        XCTAssertTrue(
            filter.matches(
                record,
                inventory: InventoryState(
                    catalogueKey: record.key,
                    hasSpool: true,
                    hasRefill: true
                )
            )
        )
    }

    func testHistoricAndDiscontinuedVisibilityAreSeparate() {
        let historic = makeRecord(availability: .historical)
        let discontinued = makeRecord(availability: .discontinued)
        var filter = LibraryFilter(includeDiscontinued: true)

        XCTAssertFalse(filter.matches(historic, inventory: nil))
        XCTAssertTrue(filter.matches(discontinued, inventory: nil))

        filter.includeHistoric = true
        filter.includeDiscontinued = false
        XCTAssertTrue(filter.matches(historic, inventory: nil))
        XCTAssertFalse(filter.matches(discontinued, inventory: nil))
    }

    func testSearchIncludesIdentifiersAndAlternateNames() {
        let record = makeRecord(alternateNames: ["Old Tangerine"])
        for query in ["TEST", "00001", "T1", "tangerine"] {
            let filter = LibraryFilter(searchText: query)
            XCTAssertTrue(filter.matches(record, inventory: nil), "Expected \(query) to match")
        }
    }

    func testOwnershipAndReplacementFilterMatrix() {
        let pla = makeRecord(family: "PLA", variant: "PLA Basic", name: "Orange")
        let petg = makeRecord(family: "PETG", variant: "PETG HF", name: "Blue")
        let spoolOnly = InventoryState(catalogueKey: pla.key, hasSpool: true)
        let refillOnly = InventoryState(catalogueKey: pla.key, hasRefill: true)
        let both = InventoryState(catalogueKey: pla.key, hasSpool: true, hasRefill: true)
        let replacement = InventoryState(catalogueKey: pla.key, needsReplacement: true)

        XCTAssertTrue(LibraryFilter(requiresSpool: true).matches(pla, inventory: spoolOnly))
        XCTAssertFalse(LibraryFilter(requiresRefill: true).matches(pla, inventory: spoolOnly))
        XCTAssertTrue(LibraryFilter(requiresRefill: true).matches(pla, inventory: refillOnly))
        XCTAssertFalse(LibraryFilter(requiresSpool: true).matches(pla, inventory: refillOnly))
        XCTAssertTrue(
            LibraryFilter(requiresSpool: true, requiresRefill: true)
                .matches(pla, inventory: both)
        )

        let replacementInPLA = LibraryFilter(scope: .replace, materialFamilies: ["PLA"])
        XCTAssertTrue(replacementInPLA.matches(pla, inventory: replacement))
        XCTAssertFalse(replacementInPLA.matches(petg, inventory: replacement))

        let searchedOwnedRefill = LibraryFilter(
            searchText: "orange",
            materialVariants: ["PLA Basic"],
            requiresRefill: true
        )
        XCTAssertTrue(searchedOwnedRefill.matches(pla, inventory: refillOnly))
        XCTAssertFalse(searchedOwnedRefill.matches(pla, inventory: spoolOnly))
        XCTAssertFalse(searchedOwnedRefill.matches(petg, inventory: refillOnly))
    }

    func testUncertainEntriesStayHiddenUnlessTracked() {
        for availability in [CatalogueAvailability.reviewNeeded, .unknown] {
            let record = makeRecord(availability: availability)
            XCTAssertFalse(LibraryFilter().matches(record, inventory: nil))
            XCTAssertTrue(
                LibraryFilter().matches(
                    record,
                    inventory: InventoryState(catalogueKey: record.key, hasSpool: true)
                )
            )
            XCTAssertTrue(
                LibraryFilter(scope: .replace).matches(
                    record,
                    inventory: InventoryState(catalogueKey: record.key, needsReplacement: true)
                )
            )
            var reviewFilter = LibraryFilter(includeReviewNeeded: true)
            XCTAssertTrue(reviewFilter.matches(record, inventory: nil))
            reviewFilter.clearSecondaryFilters()
            XCTAssertFalse(reviewFilter.matches(record, inventory: nil))
        }
    }

    func testInventoryTotalsFollowVisibleRecordsAndCountBothFormsSeparately() {
        let pla = makeRecord(key: "PLA:1", family: "PLA", name: "Orange")
        let petg = makeRecord(key: "PETG:1", family: "PETG", name: "Blue")
        let abs = makeRecord(key: "ABS:1", family: "ABS", name: "Black")
        let records = [pla, petg, abs]
        let states = [
            InventoryState(catalogueKey: pla.key, hasSpool: true, hasRefill: true),
            InventoryState(catalogueKey: petg.key, hasRefill: true),
            InventoryState(catalogueKey: abs.key, needsReplacement: true),
        ]
        let byKey = Dictionary(uniqueKeysWithValues: states.map { ($0.catalogueKey, $0) })

        func totals(for filter: LibraryFilter) -> InventoryTotals {
            let visible = records.filter { filter.matches($0, inventory: byKey[$0.key]) }
            return InventoryTotals(records: visible, inventoryByKey: byKey)
        }

        XCTAssertEqual(totals(for: LibraryFilter(scope: .inventory)).spools, 1)
        XCTAssertEqual(totals(for: LibraryFilter(scope: .inventory)).refills, 2)
        XCTAssertEqual(
            totals(for: LibraryFilter(scope: .inventory, materialFamilies: ["PLA"])).refills,
            1
        )
        XCTAssertEqual(
            totals(for: LibraryFilter(scope: .inventory, searchText: "blue")).spools,
            0
        )
        XCTAssertEqual(
            totals(for: LibraryFilter(scope: .inventory, searchText: "not found")).refills,
            0
        )
    }

    private func makeRecord(
        key: String = "TEST:00001",
        family: String = "PLA",
        variant: String = "PLA Basic",
        name: String = "Orange",
        alternateNames: [String] = [],
        availability: CatalogueAvailability = .active
    ) -> FilamentCatalogueRecord {
        let url = URL(string: "https://au.store.bambulab.com/products/test")!
        return FilamentCatalogueRecord(
            entry: CatalogueEntry(
                key: key,
                manufacturer: "Bambu Lab",
                profileId: "TEST",
                colourVariantId: "00001",
                colourCode: "T1",
                materialFamily: family,
                materialVariant: variant,
                name: name,
                alternateNames: alternateNames,
                swatchType: .solid,
                colours: ["#FF6A13FF"],
                availability: availability,
                soldAs: .both,
                productURL: url,
                firstSeen: "1",
                lastSeenActive: "1970-01-01",
                sourceEvidence: SourceEvidence(
                    studioPath: "fixture",
                    australianStoreURL: url,
                    note: nil
                )
            ),
            catalogueVersion: "1"
        )
    }
}
