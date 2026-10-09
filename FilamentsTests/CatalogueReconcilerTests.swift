import Foundation
import SwiftData
import XCTest
@testable import Filaments

@MainActor
final class CatalogueReconcilerTests: XCTestCase {
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

        defaultsSuiteName = "CatalogueReconcilerTests.\(UUID().uuidString)"
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

    func testFirstImportCreatesCatalogueWithoutInventoryRows() throws {
        let document = makeDocument(version: "1", entries: [makeEntry(index: 0)])

        try CatalogueReconciler.reconcileIfNeeded(
            document: document,
            context: context,
            defaults: defaults
        )

        let catalogue = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        let inventory = try context.fetch(FetchDescriptor<InventoryState>())
        XCTAssertEqual(catalogue.map(\.key), ["TEST:00000"])
        XCTAssertTrue(inventory.isEmpty)
        XCTAssertEqual(defaults.string(forKey: CatalogueReconciler.importedVersionKey), "1")
    }

    func testCatalogueUpdatePreservesEveryInventoryFlagCombination() throws {
        let originalEntries = (0..<8).map { makeEntry(index: $0) }
        try importDocument(version: "1", entries: originalEntries)

        for index in 0..<8 {
            context.insert(
                InventoryState(
                    catalogueKey: originalEntries[index].key,
                    hasSpool: index & 1 != 0,
                    hasRefill: index & 2 != 0,
                    needsReplacement: index & 4 != 0
                )
            )
        }
        try context.save()

        var updatedEntries = originalEntries.enumerated().map { index, entry in
            makeEntry(
                index: index,
                name: "Renamed \(entry.name)",
                colour: "#112233FF",
                availability: index == 0 ? .discontinued : .active
            )
        }
        updatedEntries.append(makeEntry(index: 8, name: "New colour"))
        try importDocument(version: "2", entries: updatedEntries)

        let states = try context.fetch(FetchDescriptor<InventoryState>())
        XCTAssertEqual(states.count, 8)
        for state in states {
            let index = Int(state.catalogueKey.suffix(5))!
            XCTAssertEqual(state.hasSpool, index & 1 != 0)
            XCTAssertEqual(state.hasRefill, index & 2 != 0)
            XCTAssertEqual(state.needsReplacement, index & 4 != 0)
        }

        let catalogue = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        XCTAssertEqual(catalogue.count, 9)
        XCTAssertTrue(
            catalogue
                .filter { $0.key != "TEST:00008" }
                .allSatisfy { $0.name.hasPrefix("Renamed") }
        )
        XCTAssertTrue(
            catalogue
                .filter { $0.key != "TEST:00008" }
                .allSatisfy { $0.colours == ["#112233FF"] }
        )
    }

    func testMissingEntryIsRetainedAndMarkedForReview() throws {
        let retained = makeEntry(index: 0)
        let missing = makeEntry(index: 1)
        try importDocument(version: "1", entries: [retained, missing])
        context.insert(
            InventoryState(
                catalogueKey: missing.key,
                hasSpool: true,
                needsReplacement: true
            )
        )
        try context.save()

        try importDocument(version: "2", entries: [retained])

        let records = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        let missingRecord = try XCTUnwrap(records.first { $0.key == missing.key })
        XCTAssertFalse(missingRecord.isPresentInBundledCatalogue)
        XCTAssertEqual(missingRecord.availability, .reviewNeeded)

        let state = try XCTUnwrap(
            context.fetch(FetchDescriptor<InventoryState>()).first { $0.catalogueKey == missing.key }
        )
        XCTAssertTrue(state.hasSpool)
        XCTAssertTrue(state.needsReplacement)
    }

    func testReintroducedEntryBecomesActiveAgain() throws {
        let entry = makeEntry(index: 0)
        try importDocument(version: "1", entries: [entry])
        try importDocument(version: "2", entries: [])

        let returned = makeEntry(index: 0, name: "Returned", availability: .active)
        try importDocument(version: "3", entries: [returned])

        let record = try XCTUnwrap(context.fetch(FetchDescriptor<FilamentCatalogueRecord>()).first)
        XCTAssertTrue(record.isPresentInBundledCatalogue)
        XCTAssertEqual(record.availability, .active)
        XCTAssertEqual(record.name, "Returned")
    }

    func testUnsupportedSchemaDoesNotMutateExistingDataOrVersion() throws {
        let entry = makeEntry(index: 0)
        try importDocument(version: "1", entries: [entry])

        let unsupported = makeDocument(schemaVersion: 99, version: "2", entries: [])
        XCTAssertThrowsError(
            try CatalogueReconciler.reconcileIfNeeded(
                document: unsupported,
                context: context,
                defaults: defaults
            )
        )

        let record = try XCTUnwrap(context.fetch(FetchDescriptor<FilamentCatalogueRecord>()).first)
        XCTAssertEqual(record.name, entry.name)
        XCTAssertTrue(record.isPresentInBundledCatalogue)
        XCTAssertEqual(defaults.string(forKey: CatalogueReconciler.importedVersionKey), "1")
    }

    func testFailedCatalogueSaveRollsBackEveryChangeAndKeepsImportedVersion() throws {
        let retained = makeEntry(index: 0, name: "Original retained")
        let wouldBeMissing = makeEntry(index: 1, name: "Original missing")
        try importDocument(version: "1", entries: [retained, wouldBeMissing])
        context.insert(
            InventoryState(
                catalogueKey: wouldBeMissing.key,
                hasRefill: true,
                needsReplacement: true,
                lastModified: Date(timeIntervalSince1970: 10)
            )
        )
        try context.save()

        let update = makeDocument(
            version: "2",
            entries: [
                makeEntry(index: 0, name: "Renamed during failed import"),
                makeEntry(index: 2, name: "Inserted during failed import"),
            ]
        )
        XCTAssertThrowsError(
            try CatalogueReconciler.reconcileIfNeeded(
                document: update,
                context: context,
                defaults: defaults,
                save: { _ in throw PersistenceTestError.saveFailed }
            )
        ) { error in
            XCTAssertEqual(error as? PersistenceTestError, .saveFailed)
        }

        let records = try context.fetch(FetchDescriptor<FilamentCatalogueRecord>())
        XCTAssertEqual(Set(records.map(\.key)), [retained.key, wouldBeMissing.key])
        XCTAssertEqual(records.first { $0.key == retained.key }?.name, "Original retained")
        XCTAssertEqual(records.first { $0.key == wouldBeMissing.key }?.name, "Original missing")
        XCTAssertTrue(records.allSatisfy(\.isPresentInBundledCatalogue))
        XCTAssertTrue(records.allSatisfy { $0.availability == .active })

        let inventory = try XCTUnwrap(
            context.fetch(FetchDescriptor<InventoryState>()).first {
                $0.catalogueKey == wouldBeMissing.key
            }
        )
        XCTAssertTrue(inventory.hasRefill)
        XCTAssertTrue(inventory.needsReplacement)
        XCTAssertEqual(inventory.lastModified, Date(timeIntervalSince1970: 10))
        XCTAssertEqual(defaults.string(forKey: CatalogueReconciler.importedVersionKey), "1")
    }

    func testMalformedJSONIsRejectedBeforeImport() {
        let malformed = Data(#"{"schemaVersion": 1, "entries": [}"#.utf8)
        XCTAssertThrowsError(try BundledCatalogue.decode(malformed))
    }

    func testValidatorRejectsInvalidDocumentMetadata() {
        assertValidationError(
            makeDocument(version: " ", entries: []),
            equals: .missingDocumentField("catalogueVersion")
        )
        assertValidationError(
            makeDocument(version: "1", entries: [], generatorVersion: "\n"),
            equals: .missingDocumentField("generatorVersion")
        )
        assertValidationError(
            makeDocument(version: "1", entries: [], studioRevision: String(repeating: "A", count: 40)),
            equals: .invalidStudioRevision(String(repeating: "A", count: 40))
        )
        assertValidationError(
            makeDocument(
                version: "1",
                entries: [],
                retrievalDates: [
                    "bambuStudio": "2026-02-30",
                    "australianStore": "2026-10-03",
                ]
            ),
            equals: .invalidSourceRetrievalDate("bambuStudio")
        )
        assertValidationError(
            makeDocument(
                version: "1",
                entries: [],
                checksum: String(repeating: "F", count: 64)
            ),
            equals: .invalidContentChecksum(String(repeating: "F", count: 64))
        )
    }

    func testValidatorRejectsInvalidEntryMetadataAndStoreOrigins() {
        assertValidationError(
            makeDocument(version: "1", entries: [makeEntry(index: 0, manufacturer: "Other")]),
            equals: .wrongManufacturer(key: "TEST:00000", manufacturer: "Other")
        )
        assertValidationError(
            makeDocument(version: "1", entries: [makeEntry(index: 0, colourCode: " ")]),
            equals: .missingField(key: "TEST:00000", field: "colourCode")
        )
        assertValidationError(
            makeDocument(version: "1", entries: [makeEntry(index: 0, studioPath: "")]),
            equals: .missingField(key: "TEST:00000", field: "sourceEvidence.studioPath")
        )
        assertValidationError(
            makeDocument(version: "1", entries: [makeEntry(index: 0, alternateNames: [" "])]),
            equals: .invalidAlternateName("TEST:00000")
        )
        assertValidationError(
            makeDocument(version: "1", entries: [makeEntry(index: 0, lastSeenActive: "2026-02-30")]),
            equals: .invalidLastSeenActive("TEST:00000")
        )
        assertValidationError(
            makeDocument(
                version: "1",
                entries: [
                    makeEntry(
                        index: 0,
                        productURL: URL(string: "http://au.store.bambulab.com/products/test")!
                    ),
                ]
            ),
            equals: .invalidAustralianStoreURL(key: "TEST:00000", field: "productURL")
        )
        assertValidationError(
            makeDocument(
                version: "1",
                entries: [
                    makeEntry(
                        index: 0,
                        evidenceURL: URL(string: "https://example.com/products/test")!
                    ),
                ]
            ),
            equals: .invalidAustralianStoreURL(
                key: "TEST:00000",
                field: "sourceEvidence.australianStoreURL"
            )
        )
    }

    func testValidatorRejectsNonASCIIHexColours() {
        let entry = makeEntry(index: 0, colour: "#ＡABBCCFF")
        assertValidationError(
            makeDocument(version: "1", entries: [entry]),
            equals: .invalidColour(key: entry.key, colour: "#ＡABBCCFF")
        )
    }

    func testDecoderIgnoresUnknownDocumentAndEntryFields() throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let encoded = try encoder.encode(
            makeDocument(version: "1", entries: [makeEntry(index: 0)])
        )
        var object = try XCTUnwrap(
            JSONSerialization.jsonObject(with: encoded) as? [String: Any]
        )
        object["futureDocumentField"] = ["enabled": true]
        var entries = try XCTUnwrap(object["entries"] as? [[String: Any]])
        entries[0]["futureEntryField"] = "preserved upstream, ignored by this app"
        var evidence = try XCTUnwrap(entries[0]["sourceEvidence"] as? [String: Any])
        evidence["futureEvidenceField"] = 1
        entries[0]["sourceEvidence"] = evidence
        object["entries"] = entries

        let decoded = try BundledCatalogue.decode(
            JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        )

        XCTAssertEqual(decoded.catalogueVersion, "1")
        XCTAssertEqual(decoded.entries.map(\.key), ["TEST:00000"])
    }

    func testInventoryDraftReflectsAndAppliesEveryFlag() {
        let state = InventoryState(
            catalogueKey: "TEST:00000",
            hasSpool: true,
            needsReplacement: true,
            lastModified: Date(timeIntervalSince1970: 1)
        )
        var draft = InventoryDraft(state: state)

        XCTAssertTrue(draft.hasSpool)
        XCTAssertFalse(draft.hasRefill)
        XCTAssertTrue(draft.needsReplacement)
        XCTAssertFalse(draft.differs(from: state))

        draft.hasSpool = false
        draft.hasRefill = true
        let modifiedAt = Date(timeIntervalSince1970: 2)
        XCTAssertTrue(draft.differs(from: state))
        draft.apply(to: state, modifiedAt: modifiedAt)

        XCTAssertFalse(state.hasSpool)
        XCTAssertTrue(state.hasRefill)
        XCTAssertTrue(state.needsReplacement)
        XCTAssertEqual(state.lastModified, modifiedAt)
        XCTAssertFalse(draft.differs(from: state))
    }

    func testEmptyInventoryDraftDoesNotRequireAStoredState() {
        var draft = InventoryDraft(state: nil)

        XCTAssertFalse(draft.hasAnySelection)
        XCTAssertFalse(draft.differs(from: nil))

        draft.needsReplacement = true
        XCTAssertTrue(draft.hasAnySelection)
        XCTAssertTrue(draft.differs(from: nil))
    }

    func testInventoryDraftPersistsInsertAndUpdateThroughSwiftData() throws {
        let initialModifiedAt = Date(timeIntervalSince1970: 10)
        var draft = InventoryDraft(state: nil)
        draft.hasSpool = true
        draft.needsReplacement = true

        let inserted = try XCTUnwrap(
            draft.persist(
                catalogueKey: "TEST:00000",
                existing: nil,
                context: context,
                modifiedAt: initialModifiedAt
            )
        )
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<InventoryState>()), 1)
        XCTAssertTrue(inserted.hasSpool)
        XCTAssertFalse(inserted.hasRefill)
        XCTAssertTrue(inserted.needsReplacement)
        XCTAssertEqual(inserted.lastModified, initialModifiedAt)

        var update = InventoryDraft(state: inserted)
        update.hasSpool = false
        update.hasRefill = true
        let updatedModifiedAt = Date(timeIntervalSince1970: 20)
        let updated = try XCTUnwrap(
            update.persist(
                catalogueKey: inserted.catalogueKey,
                existing: inserted,
                context: context,
                modifiedAt: updatedModifiedAt
            )
        )

        XCTAssertTrue(updated === inserted)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<InventoryState>()), 1)
        XCTAssertFalse(updated.hasSpool)
        XCTAssertTrue(updated.hasRefill)
        XCTAssertTrue(updated.needsReplacement)
        XCTAssertEqual(updated.lastModified, updatedModifiedAt)
    }

    func testEmptyAndUnchangedDraftsDoNotWriteInventory() throws {
        let emptyDraft = InventoryDraft(state: nil)
        XCTAssertNil(
            try emptyDraft.persist(
                catalogueKey: "TEST:00000",
                existing: nil,
                context: context
            )
        )
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<InventoryState>()), 0)

        let originalModifiedAt = Date(timeIntervalSince1970: 10)
        let existing = InventoryState(
            catalogueKey: "TEST:00001",
            hasRefill: true,
            lastModified: originalModifiedAt
        )
        context.insert(existing)
        try context.save()
        let unchanged = InventoryDraft(state: existing)

        let result = try unchanged.persist(
            catalogueKey: existing.catalogueKey,
            existing: existing,
            context: context,
            modifiedAt: Date(timeIntervalSince1970: 20)
        )

        XCTAssertTrue(result === existing)
        XCTAssertEqual(existing.lastModified, originalModifiedAt)
        XCTAssertEqual(try context.fetchCount(FetchDescriptor<InventoryState>()), 1)
    }

    func testFailedInventoryInsertRollsBackWithoutCreatingARecord() throws {
        var draft = InventoryDraft(state: nil)
        draft.hasSpool = true

        XCTAssertThrowsError(
            try draft.persist(
                catalogueKey: "TEST:00000",
                existing: nil,
                context: context,
                save: { _ in throw PersistenceTestError.saveFailed }
            )
        ) { error in
            XCTAssertEqual(error as? PersistenceTestError, .saveFailed)
        }

        XCTAssertEqual(try context.fetchCount(FetchDescriptor<InventoryState>()), 0)
    }

    func testFailedInventoryUpdateRestoresPersistedFlagsAndTimestamp() throws {
        let originalModifiedAt = Date(timeIntervalSince1970: 10)
        let existing = InventoryState(
            catalogueKey: "TEST:00000",
            hasSpool: true,
            lastModified: originalModifiedAt
        )
        context.insert(existing)
        try context.save()

        var draft = InventoryDraft(state: existing)
        draft.hasSpool = false
        draft.hasRefill = true
        draft.needsReplacement = true
        XCTAssertThrowsError(
            try draft.persist(
                catalogueKey: existing.catalogueKey,
                existing: existing,
                context: context,
                modifiedAt: Date(timeIntervalSince1970: 20),
                save: { _ in throw PersistenceTestError.saveFailed }
            )
        ) { error in
            XCTAssertEqual(error as? PersistenceTestError, .saveFailed)
        }

        let restored = try XCTUnwrap(context.fetch(FetchDescriptor<InventoryState>()).first)
        XCTAssertTrue(restored.hasSpool)
        XCTAssertFalse(restored.hasRefill)
        XCTAssertFalse(restored.needsReplacement)
        XCTAssertEqual(restored.lastModified, originalModifiedAt)
    }

    func testCatalogueSourceLinksUsePinnedStudioRevision() {
        let revision = "da8b44ee34dd349f2ae0df3f1cbae366df482354"

        XCTAssertEqual(
            CatalogueSourceLinks.colourData(revision: revision).absoluteString,
            "https://github.com/bambulab/BambuStudio/blob/\(revision)/resources/profiles/BBL/filament/filaments_color_codes.json"
        )
        XCTAssertEqual(
            CatalogueSourceLinks.licence(revision: revision).absoluteString,
            "https://github.com/bambulab/BambuStudio/blob/\(revision)/LICENSE"
        )
    }

    func testCatalogueSourceLinksRejectUnpinnedRevision() {
        XCTAssertEqual(
            CatalogueSourceLinks.colourData(revision: "master"),
            CatalogueSourceLinks.repository
        )
        XCTAssertEqual(
            CatalogueSourceLinks.licence(revision: nil),
            CatalogueSourceLinks.repository
        )
        XCTAssertEqual(
            CatalogueSourceLinks.licence(revision: String(repeating: "١", count: 40)),
            CatalogueSourceLinks.repository
        )
    }

    private func importDocument(version: String, entries: [CatalogueEntry]) throws {
        try CatalogueReconciler.reconcileIfNeeded(
            document: makeDocument(version: version, entries: entries),
            context: context,
            defaults: defaults
        )
    }

    private func makeDocument(
        schemaVersion: Int = 1,
        version: String,
        entries: [CatalogueEntry],
        generatorVersion: String = "test",
        studioRevision: String = "0000000000000000000000000000000000000000",
        retrievalDates: [String: String] = [
            "bambuStudio": "1970-01-01",
            "australianStore": "1970-01-01",
        ],
        checksum: String? = nil
    ) -> CatalogueDocument {
        CatalogueDocument(
            schemaVersion: schemaVersion,
            catalogueVersion: version,
            generatedAt: Date(timeIntervalSince1970: 0),
            region: "AU",
            generatorVersion: generatorVersion,
            sourceStudioRevision: studioRevision,
            sourceRetrievalDates: retrievalDates,
            entryCount: entries.count,
            contentChecksum: checksum,
            entries: entries
        )
    }

    private func makeEntry(
        index: Int,
        name: String? = nil,
        colour: String = "#AABBCCFF",
        availability: CatalogueAvailability = .active,
        manufacturer: String = "Bambu Lab",
        colourCode: String? = nil,
        alternateNames: [String] = [],
        lastSeenActive: String? = "1970-01-01",
        productURL: URL? = URL(string: "https://au.store.bambulab.com/products/test")!,
        studioPath: String? = nil,
        evidenceURL: URL? = URL(string: "https://au.store.bambulab.com/products/test")!
    ) -> CatalogueEntry {
        let colourVariantId = String(format: "%05d", index)
        return CatalogueEntry(
            key: "TEST:\(colourVariantId)",
            manufacturer: manufacturer,
            profileId: "TEST",
            colourVariantId: colourVariantId,
            colourCode: colourCode ?? "T\(index)",
            materialFamily: "PLA",
            materialVariant: "PLA Test",
            name: name ?? "Colour \(index)",
            alternateNames: alternateNames,
            swatchType: .solid,
            colours: [colour],
            availability: availability,
            soldAs: .both,
            productURL: productURL,
            firstSeen: "1",
            lastSeenActive: lastSeenActive,
            sourceEvidence: SourceEvidence(
                studioPath: studioPath ?? "fixture:\(index)",
                australianStoreURL: evidenceURL,
                note: nil
            )
        )
    }

    private func assertValidationError(
        _ document: CatalogueDocument,
        equals expected: CatalogueValidationError,
        file: StaticString = #filePath,
        line: UInt = #line
    ) {
        XCTAssertThrowsError(try CatalogueValidator.validate(document), file: file, line: line) { error in
            XCTAssertEqual(error as? CatalogueValidationError, expected, file: file, line: line)
        }
    }

    private enum PersistenceTestError: Error, Equatable {
        case saveFailed
    }
}
