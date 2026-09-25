import SwiftUI
import CoreText

enum VideoPart: String, CaseIterable {
    case full = "Full"
    case top = "Top"
    case bottom = "Bottom"

    var fontName: String { "Default" + rawValue }
    var rows: CGFloat { self == .full ? 54 : 27 }
    var alignment: Alignment {
        switch self {
        case .full: return .center
        case .top: return .bottom
        case .bottom: return .top
        }
    }
}

/// The system timer supplies seconds; the bundled font selects one of 30 images.
/// Keep the dynamic Text intact: fixedSize and clipping failed on the real Watch.
struct VideoView: View {
    let text: Text
    var part: VideoPart = .full
    var customFont: CTFont? = nil

    var body: some View {
        GeometryReader { geometry in
            let cell = max(0, min((geometry.size.width - 2) / 96,
                                  (geometry.size.height - 2) / part.rows))
            ZStack(alignment: part.alignment) {
                Color.black
                text
                    .font(customFont.map { Font(CTFontCreateCopyWithAttributes($0, cell * 64, nil, nil)) }
                        ?? .custom(part.fontName + "-Regular", fixedSize: cell * 64))
                    .lineLimit(1)
                    .foregroundStyle(.white)
                    .environment(\.locale, Locale(identifier: "en_US_POSIX"))
                    .environment(\.layoutDirection, .leftToRight)
                    .accessibilityLabel("30-second video")
            }
        }
    }
}
