import Foundation

enum BundledCatalogueError: LocalizedError {
    case missingResource

    var errorDescription: String? {
        "The bundled filament catalogue couldn't be found."
    }
}

enum BundledCatalogue {
    static func load(bundle: Bundle = .main) throws -> CatalogueDocument {
        guard let url = bundle.url(forResource: "catalogue", withExtension: "json") else {
            throw BundledCatalogueError.missingResource
        }

        return try decode(Data(contentsOf: url))
    }

    static func decode(_ data: Data) throws -> CatalogueDocument {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let document = try decoder.decode(CatalogueDocument.self, from: data)
        try CatalogueValidator.validate(document)
        return document
    }
}
