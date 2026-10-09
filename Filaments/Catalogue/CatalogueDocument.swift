import Foundation

enum CatalogueAvailability: String, Codable, CaseIterable, Sendable {
    case active
    case discontinued
    case reviewNeeded
    case historical
    case unknown

    var displayName: String {
        switch self {
        case .active: "Active"
        case .discontinued: "Discontinued"
        case .reviewNeeded: "Review needed"
        case .historical: "Historical"
        case .unknown: "Unknown"
        }
    }
}

enum CatalogueSwatchType: String, Codable, Sendable {
    case solid
    case gradient
    case multicolour
    case translucent

    var accessibilityName: String {
        switch self {
        case .solid: "Solid colour"
        case .gradient: "Gradient colour"
        case .multicolour: "Multicolour"
        case .translucent: "Translucent colour"
        }
    }
}

enum PackagingAvailability: String, Codable, Sendable {
    case spool
    case refill
    case both

    var displayName: String {
        switch self {
        case .spool: "Spool"
        case .refill: "Refill"
        case .both: "Spool and refill"
        }
    }
}

struct CatalogueDocument: Codable, Sendable {
    let schemaVersion: Int
    let catalogueVersion: String
    let generatedAt: Date
    let region: String
    let generatorVersion: String
    let sourceStudioRevision: String
    let sourceRetrievalDates: [String: String]
    let entryCount: Int
    let contentChecksum: String?
    let entries: [CatalogueEntry]
}

struct CatalogueEntry: Codable, Identifiable, Sendable {
    var id: String { key }

    let key: String
    let manufacturer: String
    let profileId: String
    let colourVariantId: String
    let colourCode: String
    let materialFamily: String
    let materialVariant: String
    let name: String
    let alternateNames: [String]
    let swatchType: CatalogueSwatchType
    let colours: [String]
    let availability: CatalogueAvailability
    let soldAs: PackagingAvailability
    let productURL: URL?
    let firstSeen: String
    let lastSeenActive: String?
    let sourceEvidence: SourceEvidence
}

struct SourceEvidence: Codable, Sendable {
    let studioPath: String
    let australianStoreURL: URL?
    let note: String?
}
