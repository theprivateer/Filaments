import Foundation
import SwiftData
import XCTest
@testable import Filaments

@MainActor
final class FullCataloguePerformanceTests: XCTestCase {
    private let importBudget: TimeInterval = 5
    private let updateBudget: TimeInterval = 5
    private let filterBudget: TimeInterval = 1

    private var container: ModelContainer!
    private var context: ModelContext!
    private var defaults: UserDefaults!
    private var defaultsSuiteName: String!

    override func setUpWithError() throws {
        let configuration = ModelConfiguration(isStoredInMemoryOnly: true)
        container = try ModelContainer(
            for: FilamentCatalogueRecord.self,
            InventoryState.self,
            configurations: configuration
        )
        context = container.mainContext

        defaultsSuiteName = "FullCataloguePerformanceTests.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: defaultsSuiteName)
        defaults.removePersistentDomain(forName: defaultsSuiteName)
    }

    override func tearDownWithError() throws {
        defaults.removePersistentDomain(forName: defaultsSuiteName)
        defaults = nil
        defaultsSuiteName = nil
        context = nil
        container = nil
    }

    func testDraftCatalogueImportUpdateAndFilteringStayWithinBudgets() throws {
        let document = try loadDraftCatalogue()
        XCTAssertEqual(document.entries.count, 274)

        let swatchCounts = Dictionary(
            grouping: document.entries,
            by: { $0.swatchType.rawValue }
        ).mapValues(\.count)
        XCTAssertEqual(swatchCounts["solid"], 230)
        XCTAssertEqual(swatchCounts["translucent"], 24)
        XCTAssertEqual(swatchCounts["gradient"], 13)
        XCTAssertEqual(swatchCounts["multicolour"], 7)

        let importDuration = try elapsed {
            try CatalogueReconciler.reconcileIfNeeded(
                document: document,
                context: context,
                defaults: defaults
            )
        }

        let importedRecords = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        XCTAssertEqual(importedRecords.count, document.entries.count)

        for (index, entry) in document.entries.enumerated() where index.isMultiple(of: 3) {
            context.insert(
                InventoryState(
                    catalogueKey: entry.key,
                    hasSpool: index.isMultiple(of: 2),
                    hasRefill: !index.isMultiple(of: 2),
                    needsReplacement: index.isMultiple(of: 5)
                )
            )
        }
        try context.save()

        let update = CatalogueDocument(
            schemaVersion: document.schemaVersion,
            catalogueVersion: "\(document.catalogueVersion)-performance-update",
            generatedAt: document.generatedAt,
            region: document.region,
            generatorVersion: document.generatorVersion,
            sourceStudioRevision: document.sourceStudioRevision,
            sourceRetrievalDates: document.sourceRetrievalDates,
            entryCount: document.entryCount,
            contentChecksum: document.contentChecksum,
            entries: document.entries
        )
        let updateDuration = try elapsed {
            try CatalogueReconciler.reconcileIfNeeded(
                document: update,
                context: context,
                defaults: defaults
            )
        }

        let inventory = try context.fetch(FetchDescriptor<InventoryState>())
        XCTAssertEqual(inventory.count, 92)
        XCTAssertTrue(inventory.allSatisfy { $0.hasSpool != $0.hasRefill })

        let inventoryByKey = Dictionary(
            uniqueKeysWithValues: inventory.map { ($0.catalogueKey, $0) }
        )
        let filter = LibraryFilter(
            searchText: "red",
            materialFamilies: ["PLA", "PETG"],
            includeDiscontinued: true
        )
        var totalMatches = 0
        let filterDuration = elapsed {
            for _ in 0..<250 {
                totalMatches += importedRecords.lazy.filter {
                    filter.matches($0, inventory: inventoryByKey[$0.key])
                }.count
            }
        }

        XCTAssertGreaterThan(totalMatches, 0)
        XCTAssertLessThan(importDuration, importBudget)
        XCTAssertLessThan(updateDuration, updateBudget)
        XCTAssertLessThan(filterDuration, filterBudget)

        print(
            String(
                format: "PERFORMANCE 274 entries: import %.3fs, update %.3fs, 250 filter passes %.3fs",
                importDuration,
                updateDuration,
                filterDuration
            )
        )
    }

    private func loadDraftCatalogue() throws -> CatalogueDocument {
        let bundle = Bundle(for: Self.self)
        let url = try XCTUnwrap(
            bundle.url(forResource: "2026.10.02.2-draft", withExtension: "json")
        )
        return try BundledCatalogue.decode(Data(contentsOf: url))
    }

    private func elapsed(_ operation: () throws -> Void) rethrows -> TimeInterval {
        let start = Date()
        try operation()
        return Date().timeIntervalSince(start)
    }
}
