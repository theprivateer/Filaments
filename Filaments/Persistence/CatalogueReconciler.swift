import Foundation
import SwiftData

@MainActor
enum CatalogueReconciler {
    static let importedVersionKey = "importedCatalogueVersion"

    static func reconcileIfNeeded(
        document: CatalogueDocument,
        context: ModelContext,
        defaults: UserDefaults = .standard,
        save: (ModelContext) throws -> Void = { try $0.save() }
    ) throws {
        try CatalogueValidator.validate(document)

        let importedVersion = defaults.string(forKey: importedVersionKey)
        let existingRecords = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        guard importedVersion != document.catalogueVersion || existingRecords.isEmpty else { return }

        let recordsByKey = Dictionary(uniqueKeysWithValues: existingRecords.map { ($0.key, $0) })

        do {
            for record in existingRecords {
                record.isPresentInBundledCatalogue = false
                record.availabilityRawValue = CatalogueAvailability.reviewNeeded.rawValue
            }

            for entry in document.entries {
                if let record = recordsByKey[entry.key] {
                    record.update(from: entry, catalogueVersion: document.catalogueVersion)
                } else {
                    context.insert(
                        FilamentCatalogueRecord(
                            entry: entry,
                            catalogueVersion: document.catalogueVersion
                        )
                    )
                }
            }

            try save(context)
            defaults.set(document.catalogueVersion, forKey: importedVersionKey)
        } catch {
            context.rollback()
            throw error
        }
    }
}
