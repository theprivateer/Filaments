import Foundation

enum LibraryScope: String, CaseIterable, Identifiable {
    case all
    case inventory
    case replace

    var id: Self { self }

    var title: String {
        switch self {
        case .all: "All"
        case .inventory: "Inventory"
        case .replace: "Replace"
        }
    }

    var systemImage: String {
        switch self {
        case .all: "square.grid.2x2"
        case .inventory: "shippingbox"
        case .replace: "arrow.triangle.2.circlepath"
        }
    }
}

struct LibraryFilter: Equatable {
    var scope: LibraryScope = .all
    var searchText = ""
    var materialFamilies = Set<String>()
    var materialVariants = Set<String>()
    var requiresSpool = false
    var requiresRefill = false
    var includeDiscontinued = false
    var includeHistoric = false
    var includeReviewNeeded = false

    var hasSecondaryFilters: Bool {
        !materialFamilies.isEmpty
            || !materialVariants.isEmpty
            || requiresSpool
            || requiresRefill
            || includeDiscontinued
            || includeHistoric
            || includeReviewNeeded
    }

    mutating func clearSecondaryFilters() {
        materialFamilies.removeAll()
        materialVariants.removeAll()
        requiresSpool = false
        requiresRefill = false
        includeDiscontinued = false
        includeHistoric = false
        includeReviewNeeded = false
    }

    func matches(_ record: FilamentCatalogueRecord, inventory: InventoryState?) -> Bool {
        matchesVisibility(record, inventory: inventory)
            && matchesScope(inventory)
            && matchesMaterials(record)
            && matchesOwnership(inventory)
            && matchesSearch(record)
    }

    private func matchesVisibility(
        _ record: FilamentCatalogueRecord,
        inventory: InventoryState?
    ) -> Bool {
        switch record.availability {
        case .active:
            return true
        case .discontinued:
            return includeDiscontinued || inventory?.isOwned == true || inventory?.needsReplacement == true
        case .historical:
            return includeHistoric || inventory?.isOwned == true || inventory?.needsReplacement == true
        case .reviewNeeded, .unknown:
            return includeReviewNeeded
                || inventory?.isOwned == true
                || inventory?.needsReplacement == true
        }
    }

    private func matchesScope(_ inventory: InventoryState?) -> Bool {
        switch scope {
        case .all: return true
        case .inventory: return inventory?.isOwned == true
        case .replace: return inventory?.needsReplacement == true
        }
    }

    private func matchesMaterials(_ record: FilamentCatalogueRecord) -> Bool {
        if !materialFamilies.isEmpty, !materialFamilies.contains(record.materialFamily) {
            return false
        }
        if !materialVariants.isEmpty, !materialVariants.contains(record.materialVariant) {
            return false
        }
        return true
    }

    private func matchesOwnership(_ inventory: InventoryState?) -> Bool {
        if requiresSpool, inventory?.hasSpool != true { return false }
        if requiresRefill, inventory?.hasRefill != true { return false }
        return true
    }

    private func matchesSearch(_ record: FilamentCatalogueRecord) -> Bool {
        let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { return true }

        let values = [
            record.name,
            record.materialFamily,
            record.materialVariant,
            record.profileId,
            record.colourVariantId,
            record.colourCode,
        ] + record.alternateNames
        return values.contains { $0.localizedCaseInsensitiveContains(query) }
    }
}

struct InventoryTotals: Equatable {
    let spools: Int
    let refills: Int

    init(
        records: [FilamentCatalogueRecord],
        inventoryByKey: [String: InventoryState]
    ) {
        var spoolCount = 0
        var refillCount = 0
        for record in records {
            guard let state = inventoryByKey[record.key] else { continue }
            if state.hasSpool { spoolCount += 1 }
            if state.hasRefill { refillCount += 1 }
        }
        spools = spoolCount
        refills = refillCount
    }
}
