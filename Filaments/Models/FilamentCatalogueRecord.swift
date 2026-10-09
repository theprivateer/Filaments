import Foundation
import SwiftData

@Model
final class FilamentCatalogueRecord {
    @Attribute(.unique) var key: String
    var manufacturer: String
    var profileId: String
    var colourVariantId: String
    var colourCode: String
    var materialFamily: String
    var materialVariant: String
    var name: String
    var alternateNames: [String]
    var swatchTypeRawValue: String
    var colours: [String]
    var availabilityRawValue: String
    var soldAsRawValue: String
    var productURLString: String?
    var firstSeen: String
    var lastSeenActive: String?
    var catalogueVersion: String
    var isPresentInBundledCatalogue: Bool

    var availability: CatalogueAvailability {
        CatalogueAvailability(rawValue: availabilityRawValue) ?? .unknown
    }

    var swatchType: CatalogueSwatchType {
        CatalogueSwatchType(rawValue: swatchTypeRawValue) ?? .solid
    }

    var soldAs: PackagingAvailability {
        PackagingAvailability(rawValue: soldAsRawValue) ?? .spool
    }

    var productURL: URL? {
        productURLString.flatMap(URL.init(string:))
    }

    init(entry: CatalogueEntry, catalogueVersion: String) {
        key = entry.key
        manufacturer = entry.manufacturer
        profileId = entry.profileId
        colourVariantId = entry.colourVariantId
        colourCode = entry.colourCode
        materialFamily = entry.materialFamily
        materialVariant = entry.materialVariant
        name = entry.name
        alternateNames = entry.alternateNames
        swatchTypeRawValue = entry.swatchType.rawValue
        colours = entry.colours
        availabilityRawValue = entry.availability.rawValue
        soldAsRawValue = entry.soldAs.rawValue
        productURLString = entry.productURL?.absoluteString
        firstSeen = entry.firstSeen
        lastSeenActive = entry.lastSeenActive
        self.catalogueVersion = catalogueVersion
        isPresentInBundledCatalogue = true
    }

    func update(from entry: CatalogueEntry, catalogueVersion: String) {
        manufacturer = entry.manufacturer
        profileId = entry.profileId
        colourVariantId = entry.colourVariantId
        colourCode = entry.colourCode
        materialFamily = entry.materialFamily
        materialVariant = entry.materialVariant
        name = entry.name
        alternateNames = entry.alternateNames
        swatchTypeRawValue = entry.swatchType.rawValue
        colours = entry.colours
        availabilityRawValue = entry.availability.rawValue
        soldAsRawValue = entry.soldAs.rawValue
        productURLString = entry.productURL?.absoluteString
        firstSeen = entry.firstSeen
        lastSeenActive = entry.lastSeenActive
        self.catalogueVersion = catalogueVersion
        isPresentInBundledCatalogue = true
    }
}

