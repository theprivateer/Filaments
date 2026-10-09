import Foundation

enum CatalogueSourceLinks {
    static let repository = URL(string: "https://github.com/bambulab/BambuStudio")!

    static func colourData(revision: String?) -> URL {
        pinnedURL(
            revision: revision,
            path: "resources/profiles/BBL/filament/filaments_color_codes.json"
        ) ?? repository
    }

    static func licence(revision: String?) -> URL {
        pinnedURL(revision: revision, path: "LICENSE") ?? repository
    }

    private static func pinnedURL(revision: String?, path: String) -> URL? {
        guard let revision, isValidRevision(revision) else { return nil }
        return URL(string: "https://github.com/bambulab/BambuStudio/blob/\(revision)/\(path)")
    }

    private static func isValidRevision(_ value: String) -> Bool {
        value.utf8.count == 40 && value.utf8.allSatisfy { byte in
            (48...57).contains(byte) || (97...102).contains(byte)
        }
    }
}
