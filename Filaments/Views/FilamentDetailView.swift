import SwiftData
import SwiftUI

struct FilamentDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext
    @Bindable var record: FilamentCatalogueRecord
    @State private var inventory: InventoryState?
    @State private var draft: InventoryDraft
    @State private var saveIssue: String?

    init(record: FilamentCatalogueRecord, inventory: InventoryState?) {
        self.record = record
        _inventory = State(initialValue: inventory)
        _draft = State(initialValue: InventoryDraft(state: inventory))
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("My inventory") {
                    FilamentSwatch(
                        colours: record.colours,
                        swatchType: record.swatchType,
                        name: record.name
                    )
                        .frame(height: 150)

                    LabeledContent("Colour") {
                        Text(record.name).readableSecondaryStyle()
                    }
                    LabeledContent("Material") {
                        Text(record.materialVariant).readableSecondaryStyle()
                    }
                    LabeledContent("Supplied as") {
                        Text(record.soldAs.displayName).readableSecondaryStyle()
                    }
                }

                Section {
                    Toggle("I have a spool", isOn: $draft.hasSpool)
                        .accessibilityIdentifier("inventory.hasSpool")
                    Toggle("I have an unmounted refill", isOn: $draft.hasRefill)
                        .accessibilityIdentifier("inventory.hasRefill")
                    Toggle("Needs replacement", isOn: $draft.needsReplacement)
                        .accessibilityIdentifier("inventory.needsReplacement")
                    Text("The replacement reminder stays set when you clear the spool and refill options.")
                        .font(.footnote)
                        .foregroundStyle(.primary)
                }

                Section("Catalogue") {
                    LabeledContent("Profile ID") {
                        Text(record.profileId).readableSecondaryStyle()
                    }
                    LabeledContent("Colour variant ID") {
                        Text(record.colourVariantId).readableSecondaryStyle()
                    }
                    LabeledContent("Colour code") {
                        Text(record.colourCode).readableSecondaryStyle()
                    }
                    LabeledContent("Availability") {
                        Text(record.availability.displayName).readableSecondaryStyle()
                    }

                    if record.availability == .discontinued {
                        Label(
                            "This filament is no longer listed in the Australian catalogue. Your inventory details are retained.",
                            systemImage: "nosign"
                        )
                        .foregroundStyle(.red)
                        .accessibilityIdentifier("catalogue.discontinuedExplanation")
                    } else if record.availability == .active, let url = record.productURL {
                        Link(destination: url) {
                            Label("View on Bambu Lab AU", systemImage: "safari")
                        }
                        .accessibilityIdentifier("catalogue.productLink")
                    }
                }
            }
            .navigationTitle(record.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done", action: saveAndDismiss)
                }
            }
            .interactiveDismissDisabled(draft.differs(from: inventory))
            .alert(
                "Couldn't save inventory",
                isPresented: Binding(
                    get: { saveIssue != nil },
                    set: { if !$0 { saveIssue = nil } }
                )
            ) {
                Button("OK", role: .cancel) {}
            } message: {
                Text(saveIssue ?? "Your changes weren't saved. Please try again.")
            }
        }
    }

    private func saveAndDismiss() {
        do {
            inventory = try draft.persist(
                catalogueKey: record.key,
                existing: inventory,
                context: modelContext,
                save: inventorySaveOperation
            )
            dismiss()
        } catch {
            saveIssue = "Your changes weren't saved. \(error.localizedDescription)"
        }
    }

    private var inventorySaveOperation: (ModelContext) throws -> Void {
#if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing-fail-inventory-save") {
            return { _ in throw UITestingInventorySaveError() }
        }
#endif
        return { try $0.save() }
    }
}

#if DEBUG
private struct UITestingInventorySaveError: LocalizedError {
    var errorDescription: String? {
        "Simulated inventory save failure."
    }
}
#endif
