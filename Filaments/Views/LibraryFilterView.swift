import SwiftUI

struct LibraryFilterView: View {
    @Environment(\.dismiss) private var dismiss
    @Binding var filter: LibraryFilter
    let materialFamilies: [String]
    let materialVariants: [String]

    var body: some View {
        NavigationStack {
            Form {
                Section("Material families") {
                    ForEach(materialFamilies, id: \.self) { family in
                        selectionToggle(family, values: $filter.materialFamilies)
                    }
                }

                Section("Material variants") {
                    ForEach(materialVariants, id: \.self) { variant in
                        selectionToggle(variant, values: $filter.materialVariants)
                    }
                }

                Section("Inventory") {
                    Toggle("Has spool", isOn: $filter.requiresSpool)
                    Toggle("Has refill", isOn: $filter.requiresRefill)
                    if filter.requiresSpool && filter.requiresRefill {
                        Text("Only entries with both forms will be shown.")
                            .font(.footnote)
                            .foregroundStyle(.primary)
                    }
                }

                Section("Availability") {
                    Toggle("Include discontinued", isOn: $filter.includeDiscontinued)
                    Toggle("Include historic", isOn: $filter.includeHistoric)
                    Toggle("Include entries needing review", isOn: $filter.includeReviewNeeded)
                }

                if filter.hasSecondaryFilters {
                    Section {
                        Button("Clear filters", role: .destructive) {
                            filter.clearSecondaryFilters()
                        }
                    }
                }
            }
            .navigationTitle("Filters")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func selectionToggle(_ value: String, values: Binding<Set<String>>) -> some View {
        Toggle(
            value,
            isOn: Binding(
                get: { values.wrappedValue.contains(value) },
                set: { selected in
                    if selected {
                        values.wrappedValue.insert(value)
                    } else {
                        values.wrappedValue.remove(value)
                    }
                }
            )
        )
        .accessibilityIdentifier("filter.option.\(value)")
    }
}
