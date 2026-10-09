import SwiftUI

struct AboutView: View {
    @Environment(\.dismiss) private var dismiss

    let catalogueVersion: String?
    let catalogueEntryCount: Int
    let sourceStudioRevision: String?

    var body: some View {
        NavigationStack {
            Form {
                Section("About Filaments") {
                    Text("Filaments is an independent inventory app. It isn't affiliated with or endorsed by Bambu Lab.")
                        .accessibilityIdentifier("about.independence")
                }

                Section("Your data") {
                    Label(
                        "Your inventory is stored only on this device. It isn't sent to Bambu Lab or an app server.",
                        systemImage: "iphone"
                    )
                    Label(
                        "The catalogue is bundled with the app. Filaments doesn't fetch store listings or live stock.",
                        systemImage: "network.slash"
                    )
                }
                .accessibilityIdentifier("about.localData")

                Section("Catalogue sources") {
                    Text("Bambu Studio provides the source identifiers and colour data. Australian availability is reviewed against the Bambu Lab AU store before a catalogue is released.")

                    Link(
                        "Bambu Studio source data",
                        destination: CatalogueSourceLinks.colourData(revision: sourceStudioRevision)
                    )
                    .accessibilityIdentifier("about.sourceData")
                    Link(
                        "Bambu Studio licence",
                        destination: CatalogueSourceLinks.licence(revision: sourceStudioRevision)
                    )
                    .accessibilityIdentifier("about.sourceLicence")
                }

                Section("Bundled catalogue") {
                    LabeledContent("Version") {
                        Text(catalogueVersion ?? "Unavailable").readableSecondaryStyle()
                    }
                    LabeledContent("Entries") {
                        Text(catalogueEntryCount.formatted()).readableSecondaryStyle()
                    }
                }
            }
            .navigationTitle("About")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

#Preview {
    AboutView(
        catalogueVersion: "2026.10.02.1",
        catalogueEntryCount: 6,
        sourceStudioRevision: "da8b44ee34dd349f2ae0df3f1cbae366df482354"
    )
}
