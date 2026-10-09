import SwiftData
import SwiftUI

struct ContentView: View {
    @Environment(\.colorScheme) private var colorScheme
    @Query(
        sort: [
            SortDescriptor(\FilamentCatalogueRecord.materialFamily),
            SortDescriptor(\FilamentCatalogueRecord.materialVariant),
            SortDescriptor(\FilamentCatalogueRecord.name),
        ]
    ) private var catalogue: [FilamentCatalogueRecord]
    @Query private var inventory: [InventoryState]

    @State private var filter = LibraryFilter()
    @State private var isShowingFilters = false
    @State private var isShowingAbout = false
    @State private var selection: FilamentSelection?

    let catalogueIssue: String?
    let catalogueSourceStudioRevision: String?

    init(catalogueIssue: String? = nil, catalogueSourceStudioRevision: String? = nil) {
        self.catalogueIssue = catalogueIssue
        self.catalogueSourceStudioRevision = catalogueSourceStudioRevision
    }

    private var inventoryByKey: [String: InventoryState] {
        Dictionary(uniqueKeysWithValues: inventory.map { ($0.catalogueKey, $0) })
    }

    private var visibleRecords: [FilamentCatalogueRecord] {
        catalogue.filter { record in
            filter.matches(record, inventory: inventoryByKey[record.key])
        }
    }

    private var materialFamilies: [String] {
        Array(Set(catalogue.map(\.materialFamily))).sorted()
    }

    private var materialVariants: [String] {
        Array(Set(catalogue.map(\.materialVariant))).sorted()
    }

    private var inventoryTotals: InventoryTotals {
        InventoryTotals(records: visibleRecords, inventoryByKey: inventoryByKey)
    }

    var body: some View {
        NavigationStack {
            Group {
                if visibleRecords.isEmpty {
                    ContentUnavailableView {
                        Label {
                            Text(emptyTitle)
                                .accessibilityIdentifier("library.emptyState.title")
                        } icon: {
                            Image(systemName: emptySystemImage)
                        }
                    } description: {
                        Text(emptyDescription)
                            .accessibilityIdentifier("library.emptyState.description")
                    }
                } else {
                    List(visibleRecords) { record in
                        Button {
                            select(record)
                        } label: {
                            FilamentRow(record: record, inventory: inventoryByKey[record.key])
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("filament.row.\(record.key)")
                    }
                    .listStyle(.plain)
                }
            }
            .navigationTitle("Filaments")
            .navigationBarTitleDisplayMode(.inline)
            .overlay(alignment: .bottom) {
                if let catalogueIssue {
                    Label(catalogueIssue, systemImage: "exclamationmark.triangle.fill")
                        .font(.footnote)
                        .foregroundStyle(.primary)
                        .padding(12)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 12))
                        .padding()
                        .accessibilityLabel("Catalogue update failed. \(catalogueIssue)")
                        .accessibilityIdentifier("library.catalogueIssue")
                }
            }
            .searchable(text: $filter.searchText, prompt: "Search filaments")
            .safeAreaInset(edge: .top) {
                VStack(spacing: 8) {
                    Picker("Library", selection: $filter.scope) {
                        ForEach(LibraryScope.allCases) { scope in
                            Label(scope.title, systemImage: scope.systemImage).tag(scope)
                        }
                    }
                    .pickerStyle(.segmented)

                    if filter.scope == .inventory {
                        Text("Spools: \(inventoryTotals.spools), Refills: \(inventoryTotals.refills)")
                        .font(.subheadline)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .accessibilityIdentifier("library.inventoryTotals")
                    }
                }
                .padding(.horizontal)
                .padding(.vertical, 8)
                .background(.bar)
            }
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        isShowingAbout = true
                    } label: {
                        Label("About", systemImage: "info.circle")
                    }
                    .accessibilityIdentifier("library.about")
#if DEBUG
                    .accessibilityValue(
                        colorScheme == .dark ? "Dark appearance" : "Light appearance"
                    )
#endif
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        isShowingFilters = true
                    } label: {
                        Label("Filters", systemImage: "line.3.horizontal.decrease.circle")
                    }
                    .tint(filter.hasSecondaryFilters ? .accentColor : nil)
                    .accessibilityIdentifier("library.filters")
                }
            }
            .sheet(item: $selection) { selection in
                FilamentDetailView(record: selection.record, inventory: selection.inventory)
            }
            .sheet(isPresented: $isShowingFilters) {
                LibraryFilterView(
                    filter: $filter,
                    materialFamilies: materialFamilies,
                    materialVariants: materialVariants
                )
            }
            .sheet(isPresented: $isShowingAbout) {
                AboutView(
                    catalogueVersion: catalogue.first?.catalogueVersion,
                    catalogueEntryCount: catalogue.count,
                    sourceStudioRevision: catalogueSourceStudioRevision
                )
            }
        }
    }

    private var emptyDescription: String {
        switch filter.scope {
        case .all: "Try changing the search or filters."
        case .inventory: "Filaments you mark as a spool or refill will appear here."
        case .replace: "Filaments marked for replacement will appear here."
        }
    }

    private var emptyTitle: String {
        filter.searchText.isEmpty ? "No filaments" : "No results"
    }

    private var emptySystemImage: String {
        filter.searchText.isEmpty ? "shippingbox" : "magnifyingglass"
    }

    private func select(_ record: FilamentCatalogueRecord) {
        selection = FilamentSelection(record: record, inventory: inventoryByKey[record.key])
    }
}

private struct FilamentSelection: Identifiable {
    let record: FilamentCatalogueRecord
    let inventory: InventoryState?

    var id: String { record.key }
}

#Preview {
    ContentView()
        .modelContainer(for: [FilamentCatalogueRecord.self, InventoryState.self], inMemory: true)
}
