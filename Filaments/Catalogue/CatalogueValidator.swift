import Foundation

enum CatalogueValidationError: LocalizedError, Equatable {
    case unsupportedSchema(Int)
    case wrongRegion(String)
    case missingDocumentField(String)
    case invalidStudioRevision(String)
    case invalidSourceRetrievalDate(String)
    case invalidContentChecksum(String)
    case entryCount(expected: Int, actual: Int)
    case duplicateKey(String)
    case invalidKey(String)
    case missingField(key: String, field: String)
    case wrongManufacturer(key: String, manufacturer: String)
    case invalidColour(key: String, colour: String)
    case invalidSwatch(key: String, reason: String)
    case invalidAlternateName(String)
    case invalidLastSeenActive(String)
    case missingAustralianEvidence(String)
    case invalidAustralianStoreURL(key: String, field: String)

    var errorDescription: String? {
        switch self {
        case let .unsupportedSchema(version):
            "Catalogue schema version \(version) isn't supported."
        case let .wrongRegion(region):
            "Expected an AU catalogue, found \(region)."
        case let .missingDocumentField(field):
            "Catalogue metadata is missing \(field)."
        case let .invalidStudioRevision(revision):
            "Catalogue Studio revision isn't a 40-character lowercase Git commit: \(revision)."
        case let .invalidSourceRetrievalDate(source):
            "Catalogue source retrieval date for \(source) isn't a valid ISO date."
        case let .invalidContentChecksum(checksum):
            "Catalogue content checksum isn't a lowercase SHA-256 digest: \(checksum)."
        case let .entryCount(expected, actual):
            "Catalogue header says \(expected) entries, but the file contains \(actual)."
        case let .duplicateKey(key):
            "Catalogue key \(key) is duplicated."
        case let .invalidKey(key):
            "Catalogue key \(key) doesn't match profileId:colourVariantId."
        case let .missingField(key, field):
            "Catalogue entry \(key) is missing \(field)."
        case let .wrongManufacturer(key, manufacturer):
            "Catalogue entry \(key) has manufacturer \(manufacturer), expected Bambu Lab."
        case let .invalidColour(key, colour):
            "Catalogue entry \(key) has an invalid colour value: \(colour)."
        case let .invalidSwatch(key, reason):
            "Catalogue entry \(key) has an invalid swatch: \(reason)."
        case let .invalidAlternateName(key):
            "Catalogue entry \(key) has a blank alternate name."
        case let .invalidLastSeenActive(key):
            "Catalogue entry \(key) has an invalid lastSeenActive date."
        case let .missingAustralianEvidence(key):
            "Active catalogue entry \(key) has no Australian store evidence."
        case let .invalidAustralianStoreURL(key, field):
            "Catalogue entry \(key) has an invalid Australian store URL in \(field)."
        }
    }
}

enum CatalogueValidator {
    static let supportedSchemaVersion = 1

    static func validate(_ document: CatalogueDocument) throws {
        guard document.schemaVersion == supportedSchemaVersion else {
            throw CatalogueValidationError.unsupportedSchema(document.schemaVersion)
        }
        guard document.region == "AU" else {
            throw CatalogueValidationError.wrongRegion(document.region)
        }
        try requireDocumentField(document.catalogueVersion, field: "catalogueVersion")
        try requireDocumentField(document.generatorVersion, field: "generatorVersion")
        guard isLowercaseHex(document.sourceStudioRevision, count: 40) else {
            throw CatalogueValidationError.invalidStudioRevision(document.sourceStudioRevision)
        }
        for source in ["bambuStudio", "australianStore"] {
            guard let value = document.sourceRetrievalDates[source], isValidISODate(value) else {
                throw CatalogueValidationError.invalidSourceRetrievalDate(source)
            }
        }
        if let checksum = document.contentChecksum, !isLowercaseHex(checksum, count: 64) {
            throw CatalogueValidationError.invalidContentChecksum(checksum)
        }
        guard document.entryCount == document.entries.count else {
            throw CatalogueValidationError.entryCount(
                expected: document.entryCount,
                actual: document.entries.count
            )
        }

        var keys = Set<String>()
        for entry in document.entries {
            guard keys.insert(entry.key).inserted else {
                throw CatalogueValidationError.duplicateKey(entry.key)
            }
            guard entry.key == "\(entry.profileId):\(entry.colourVariantId)" else {
                throw CatalogueValidationError.invalidKey(entry.key)
            }

            try require(entry.profileId, field: "profileId", key: entry.key)
            try require(entry.colourVariantId, field: "colourVariantId", key: entry.key)
            try require(entry.colourCode, field: "colourCode", key: entry.key)
            try require(entry.materialFamily, field: "materialFamily", key: entry.key)
            try require(entry.materialVariant, field: "materialVariant", key: entry.key)
            try require(entry.name, field: "name", key: entry.key)
            try require(entry.firstSeen, field: "firstSeen", key: entry.key)
            try require(entry.sourceEvidence.studioPath, field: "sourceEvidence.studioPath", key: entry.key)
            if entry.alternateNames.contains(where: {
                $0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
            }) {
                throw CatalogueValidationError.invalidAlternateName(entry.key)
            }
            if let lastSeenActive = entry.lastSeenActive, !isValidISODate(lastSeenActive) {
                throw CatalogueValidationError.invalidLastSeenActive(entry.key)
            }
            guard entry.manufacturer == "Bambu Lab" else {
                throw CatalogueValidationError.wrongManufacturer(
                    key: entry.key,
                    manufacturer: entry.manufacturer
                )
            }

            for colour in entry.colours where !isValidRGBAHex(colour) {
                throw CatalogueValidationError.invalidColour(key: entry.key, colour: colour)
            }
            if entry.colours.isEmpty {
                throw CatalogueValidationError.invalidSwatch(key: entry.key, reason: "no colours")
            }
            if [.gradient, .multicolour].contains(entry.swatchType), entry.colours.count < 2 {
                throw CatalogueValidationError.invalidSwatch(
                    key: entry.key,
                    reason: "\(entry.swatchType.rawValue) swatches need at least two colours"
                )
            }
            if entry.availability == .active, entry.sourceEvidence.australianStoreURL == nil {
                throw CatalogueValidationError.missingAustralianEvidence(entry.key)
            }
            for (field, url) in [
                ("productURL", entry.productURL),
                ("sourceEvidence.australianStoreURL", entry.sourceEvidence.australianStoreURL),
            ] {
                guard let url else { continue }
                guard isAustralianStoreURL(url) else {
                    throw CatalogueValidationError.invalidAustralianStoreURL(
                        key: entry.key,
                        field: field
                    )
                }
            }
        }
    }

    private static func requireDocumentField(_ value: String, field: String) throws {
        if value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            throw CatalogueValidationError.missingDocumentField(field)
        }
    }

    private static func require(_ value: String, field: String, key: String) throws {
        if value.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            throw CatalogueValidationError.missingField(key: key, field: field)
        }
    }

    private static func isValidRGBAHex(_ value: String) -> Bool {
        guard value.utf8.count == 9, value.utf8.first == 35 else { return false }
        return value.utf8.dropFirst().allSatisfy(isASCIIHexDigit)
    }

    private static func isLowercaseHex(_ value: String, count: Int) -> Bool {
        value.utf8.count == count && value.utf8.allSatisfy { byte in
            (48...57).contains(byte) || (97...102).contains(byte)
        }
    }

    private nonisolated static func isASCIIHexDigit(_ byte: UInt8) -> Bool {
        (48...57).contains(byte) || (65...70).contains(byte) || (97...102).contains(byte)
    }

    private static func isValidISODate(_ value: String) -> Bool {
        let formatter = DateFormatter()
        formatter.calendar = Calendar(identifier: .iso8601)
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.isLenient = false
        guard let date = formatter.date(from: value) else { return false }
        return formatter.string(from: date) == value
    }

    private static func isAustralianStoreURL(_ url: URL) -> Bool {
        url.scheme == "https" && url.host == "au.store.bambulab.com"
    }
}
