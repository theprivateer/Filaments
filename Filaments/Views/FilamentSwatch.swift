import SwiftUI

struct FilamentSwatch: View {
    let colours: [String]
    let swatchType: CatalogueSwatchType
    var name: String?

    private var resolvedColours: [Color] {
        let result = colours.compactMap { Color(rgbaHex: $0) }
        return result.isEmpty ? [.clear] : result
    }

    var body: some View {
        RoundedRectangle(cornerRadius: 12, style: .continuous)
            .fill(fillStyle)
            .overlay {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .strokeBorder(.primary.opacity(0.18), lineWidth: 1)
            }
            .accessibilityLabel(accessibilityDescription)
    }

    private var fillStyle: AnyShapeStyle {
        if resolvedColours.count == 1 {
            return AnyShapeStyle(resolvedColours[0])
        }
        return AnyShapeStyle(
            LinearGradient(
                colors: resolvedColours,
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }

    private var accessibilityDescription: String {
        let description: String
        switch swatchType {
        case .solid: description = "solid colour swatch"
        case .gradient: description = "gradient colour swatch"
        case .multicolour: description = "multicolour swatch"
        case .translucent: description = "translucent colour swatch"
        }
        return name.map { "\($0), \(description)" } ?? description.capitalized
    }
}

private extension Color {
    init?(rgbaHex: String) {
        let hex = rgbaHex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
        guard hex.count == 8, let value = UInt64(hex, radix: 16) else { return nil }

        self.init(
            .sRGB,
            red: Double((value >> 24) & 0xff) / 255,
            green: Double((value >> 16) & 0xff) / 255,
            blue: Double((value >> 8) & 0xff) / 255,
            opacity: Double(value & 0xff) / 255
        )
    }
}
