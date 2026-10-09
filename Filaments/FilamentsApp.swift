import SwiftData
import SwiftUI

@main
struct FilamentsApp: App {
    private let container: ModelContainer
    private let catalogueIssue: String?
    private let catalogueSourceStudioRevision: String?

    init() {
        do {
            container = try ModelContainer(
                for: FilamentCatalogueRecord.self,
                InventoryState.self
            )
#if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--ui-testing-reset") {
                try Self.resetStoreForUITesting(context: container.mainContext)
            }
            if ProcessInfo.processInfo.arguments.contains("--ui-testing-seed-upgrade") {
                try Self.seedPreviousCatalogueForUITesting(context: container.mainContext)
            }
#endif
        } catch {
            fatalError("Couldn't initialise Filaments: \(error.localizedDescription)")
        }

        do {
#if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--ui-testing-fail-catalogue-update") {
                throw UITestingCatalogueError.forcedUpdateFailure
            }
#endif
            let document = try BundledCatalogue.load()
            try CatalogueReconciler.reconcileIfNeeded(document: document, context: container.mainContext)
#if DEBUG
            if ProcessInfo.processInfo.arguments.contains("--ui-testing-seed-discontinued") {
                try Self.seedDiscontinuedStateForUITesting(context: container.mainContext)
            }
            if ProcessInfo.processInfo.arguments.contains("--ui-testing-seed-varied-swatches") {
                try Self.seedVariedSwatchesForUITesting(context: container.mainContext)
            }
#endif
            catalogueIssue = nil
            catalogueSourceStudioRevision = document.sourceStudioRevision
        } catch {
            let storedCatalogueCount = (try? container.mainContext.fetchCount(
                FetchDescriptor<FilamentCatalogueRecord>()
            )) ?? 0
            let hasStoredCatalogue = storedCatalogueCount > 0
            catalogueIssue = hasStoredCatalogue
                ? "The bundled catalogue couldn't be updated. Your saved catalogue and inventory are unchanged."
                : "The bundled catalogue couldn't be loaded. Please reinstall the app or contact support."
            catalogueSourceStudioRevision = nil
        }
    }

    var body: some Scene {
        WindowGroup {
            ContentView(
                catalogueIssue: catalogueIssue,
                catalogueSourceStudioRevision: catalogueSourceStudioRevision
            )
            .preferredColorScheme(uiTestingPreferredColorScheme)
        }
        .modelContainer(container)
    }

    private var uiTestingPreferredColorScheme: ColorScheme? {
#if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing-dark-appearance") {
            return .dark
        }
#endif
        return nil
    }

#if DEBUG
    private enum UITestingCatalogueError: Error {
        case forcedUpdateFailure
    }

    private static func resetStoreForUITesting(context: ModelContext) throws {
        for state in try context.fetch(FetchDescriptor<InventoryState>()) {
            context.delete(state)
        }
        for record in try context.fetch(FetchDescriptor<FilamentCatalogueRecord>()) {
            context.delete(record)
        }
        try context.save()
        UserDefaults.standard.removeObject(forKey: CatalogueReconciler.importedVersionKey)
    }

    private static func seedDiscontinuedStateForUITesting(context: ModelContext) throws {
        let records = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        guard let record = records.first(where: { $0.key == "GFA00:10300" }) else {
            return
        }
        record.availabilityRawValue = CatalogueAvailability.discontinued.rawValue
        record.productURLString = nil

        let states = try context.fetch(FetchDescriptor<InventoryState>())
        if let state = states.first(where: { $0.catalogueKey == record.key }) {
            state.hasSpool = true
            state.needsReplacement = true
            state.lastModified = .now
        } else {
            context.insert(
                InventoryState(
                    catalogueKey: record.key,
                    hasSpool: true,
                    needsReplacement: true
                )
            )
        }
        try context.save()
    }

    private static func seedPreviousCatalogueForUITesting(context: ModelContext) throws {
        let oldVersion = "2024.01.01.1"
        let sourceURL = URL(string: "https://au.store.bambulab.com/products/pla-basic-filament")!
        let currentEntry = CatalogueEntry(
            key: "GFA00:10300",
            manufacturer: "Bambu Lab",
            profileId: "GFA00",
            colourVariantId: "10300",
            colourCode: "OLD",
            materialFamily: "PLA",
            materialVariant: "PLA Legacy",
            name: "Legacy Orange",
            alternateNames: [],
            swatchType: .solid,
            colours: ["#000000FF"],
            availability: .active,
            soldAs: .spool,
            productURL: sourceURL,
            firstSeen: oldVersion,
            lastSeenActive: "2024-01-01",
            sourceEvidence: SourceEvidence(
                studioPath: "ui-test:GFA00:10300",
                australianStoreURL: sourceURL,
                note: "UI upgrade fixture"
            )
        )
        context.insert(FilamentCatalogueRecord(entry: currentEntry, catalogueVersion: oldVersion))
        context.insert(
            InventoryState(
                catalogueKey: currentEntry.key,
                hasSpool: true,
                hasRefill: true,
                needsReplacement: true
            )
        )

        let missingEntry = CatalogueEntry(
            key: "LEGACY:99999",
            manufacturer: "Bambu Lab",
            profileId: "LEGACY",
            colourVariantId: "99999",
            colourCode: "L0",
            materialFamily: "PLA",
            materialVariant: "PLA Legacy",
            name: "Legacy Blue",
            alternateNames: [],
            swatchType: .solid,
            colours: ["#0000FFFF"],
            availability: .active,
            soldAs: .refill,
            productURL: sourceURL,
            firstSeen: oldVersion,
            lastSeenActive: "2024-01-01",
            sourceEvidence: SourceEvidence(
                studioPath: "ui-test:LEGACY:99999",
                australianStoreURL: sourceURL,
                note: "UI upgrade fixture"
            )
        )
        context.insert(FilamentCatalogueRecord(entry: missingEntry, catalogueVersion: oldVersion))
        context.insert(
            InventoryState(
                catalogueKey: missingEntry.key,
                hasRefill: true,
                needsReplacement: true
            )
        )

        try context.save()
        UserDefaults.standard.set(oldVersion, forKey: CatalogueReconciler.importedVersionKey)
    }

    private static func seedVariedSwatchesForUITesting(context: ModelContext) throws {
        let records = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        let trackedKeys = ["GFA00:10900", "GFG01:32501"]
        let existingStates = try context.fetch(FetchDescriptor<InventoryState>())

        for key in trackedKeys where records.contains(where: { $0.key == key }) {
            if let state = existingStates.first(where: { $0.catalogueKey == key }) {
                state.hasSpool = true
                state.lastModified = .now
            } else {
                context.insert(InventoryState(catalogueKey: key, hasSpool: true))
            }
        }

        if !records.contains(where: { $0.key == "UITEST:00001" }) {
            let sourceURL = URL(string: "https://au.store.bambulab.com/products/pla-basic-filament")!
            let entry = CatalogueEntry(
                key: "UITEST:00001",
                manufacturer: "Bambu Lab",
                profileId: "UITEST",
                colourVariantId: "00001",
                colourCode: "T0",
                materialFamily: "PLA",
                materialVariant: "UI Test Filament",
                name: "Multicolour Test",
                alternateNames: [],
                swatchType: .multicolour,
                colours: ["#FF0000FF", "#00FF00FF", "#0000FFFF"],
                availability: .active,
                soldAs: .spool,
                productURL: sourceURL,
                firstSeen: "ui-test",
                lastSeenActive: "2026-10-05",
                sourceEvidence: SourceEvidence(
                    studioPath: "ui-test:UITEST:00001",
                    australianStoreURL: sourceURL,
                    note: "UI swatch fixture"
                )
            )
            context.insert(
                FilamentCatalogueRecord(
                    entry: entry,
                    catalogueVersion: "ui-test"
                )
            )
        }

        try context.save()
    }
#endif
}
