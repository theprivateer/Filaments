import Foundation
import SwiftData

@Model
final class InventoryState {
    @Attribute(.unique) var catalogueKey: String
    var hasSpool: Bool
    var hasRefill: Bool
    var needsReplacement: Bool
    var lastModified: Date

    var isOwned: Bool { hasSpool || hasRefill }

    init(
        catalogueKey: String,
        hasSpool: Bool = false,
        hasRefill: Bool = false,
        needsReplacement: Bool = false,
        lastModified: Date = .now
    ) {
        self.catalogueKey = catalogueKey
        self.hasSpool = hasSpool
        self.hasRefill = hasRefill
        self.needsReplacement = needsReplacement
        self.lastModified = lastModified
    }
}

struct InventoryDraft: Equatable {
    var hasSpool: Bool
    var hasRefill: Bool
    var needsReplacement: Bool

    init(state: InventoryState?) {
        hasSpool = state?.hasSpool ?? false
        hasRefill = state?.hasRefill ?? false
        needsReplacement = state?.needsReplacement ?? false
    }

    var hasAnySelection: Bool {
        hasSpool || hasRefill || needsReplacement
    }

    func differs(from state: InventoryState?) -> Bool {
        hasSpool != (state?.hasSpool ?? false)
            || hasRefill != (state?.hasRefill ?? false)
            || needsReplacement != (state?.needsReplacement ?? false)
    }

    func apply(to state: InventoryState, modifiedAt: Date = .now) {
        state.hasSpool = hasSpool
        state.hasRefill = hasRefill
        state.needsReplacement = needsReplacement
        state.lastModified = modifiedAt
    }

    @MainActor
    func persist(
        catalogueKey: String,
        existing state: InventoryState?,
        context: ModelContext,
        modifiedAt: Date = .now,
        save: (ModelContext) throws -> Void = { try $0.save() }
    ) throws -> InventoryState? {
        guard differs(from: state) else { return state }
        guard state != nil || hasAnySelection else { return nil }

        let storedState: InventoryState
        if let state {
            storedState = state
        } else {
            storedState = InventoryState(catalogueKey: catalogueKey)
            context.insert(storedState)
        }

        apply(to: storedState, modifiedAt: modifiedAt)
        do {
            try save(context)
            return storedState
        } catch {
            context.rollback()
            throw error
        }
    }
}
