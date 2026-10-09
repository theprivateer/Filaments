import SwiftUI

struct FilamentRow: View {
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize

    let record: FilamentCatalogueRecord
    let inventory: InventoryState?

    var body: some View {
        HStack(spacing: 12) {
            FilamentSwatch(
                colours: record.colours,
                swatchType: record.swatchType,
                name: record.name
            )
                .frame(width: 46, height: 46)

            VStack(alignment: .leading, spacing: 3) {
                Text(record.name)
                    .font(.headline)
                    .foregroundStyle(.primary)
                Text(record.materialVariant)
                    .font(.subheadline)
                    .readableSecondaryStyle()

                if dynamicTypeSize.isAccessibilitySize {
                    VStack(alignment: .leading, spacing: 4) {
                        statusBadges
                    }
                } else {
                    HStack(spacing: 6) {
                        statusBadges
                    }
                }
            }

            Spacer(minLength: 8)
            Image(systemName: "chevron.right")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.tertiary)
                .accessibilityHidden(true)
        }
        .contentShape(Rectangle())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(accessibilityDescription)
        .accessibilityHint("Opens filament details")
    }

    @ViewBuilder
    private var statusBadges: some View {
        if inventory?.hasSpool == true {
            StatusBadge(title: "Spool", systemImage: "cylinder")
        }
        if inventory?.hasRefill == true {
            StatusBadge(title: "Refill", systemImage: "arrow.triangle.2.circlepath")
        }
        if inventory?.needsReplacement == true {
            StatusBadge(title: "Replace", systemImage: "exclamationmark.circle", tint: .orange)
        }
        if record.availability == .discontinued {
            StatusBadge(title: "Discontinued", systemImage: "nosign", tint: .red)
        }
        if record.availability == .reviewNeeded {
            StatusBadge(title: "Review needed", systemImage: "questionmark.circle", tint: .orange)
        }
    }

    private var accessibilityDescription: String {
        var values = [record.name, record.materialVariant, record.swatchType.accessibilityName]
        if inventory?.hasSpool == true { values.append("Spool") }
        if inventory?.hasRefill == true { values.append("Refill") }
        if inventory?.needsReplacement == true { values.append("Needs replacement") }
        if record.availability == .discontinued { values.append("Discontinued") }
        if record.availability == .reviewNeeded { values.append("Review needed") }
        return values.joined(separator: ", ")
    }
}

struct StatusBadge: View {
    let title: String
    let systemImage: String
    var tint: Color = .secondary

    var body: some View {
        Label(title, systemImage: systemImage)
            .font(.caption2.weight(.medium))
            .foregroundStyle(tint)
    }
}
