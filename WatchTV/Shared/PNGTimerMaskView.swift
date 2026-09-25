import SwiftUI

/// The bundled font gates PNG frames. Only image data varies with the video.
/// Two-frame dynamic masks were verified on the physical Watch with build 16.
struct PNGTimerMaskView: View {
    let images: [CGImage]
    let clocks: [Text]
    var fontName = "FontTVGate-Regular"
    var rows: CGFloat = 54
    var alignment: Alignment = .center

    var body: some View {
        GeometryReader { geometry in
            let size = min(geometry.size.width / 96, geometry.size.height / rows) * 64
            ZStack(alignment: alignment) {
                Color.black
                ForEach(images.indices, id: \.self) { index in
                    Image(decorative: images[index], scale: 1)
                        .resizable().interpolation(.none).scaledToFit()
                        .mask {
                            clocks[index]
                                .font(.custom(fontName, fixedSize: size))
                                .foregroundStyle(.white)
                                .lineLimit(1)
                                .environment(\.locale, Locale(identifier: "en_US_POSIX"))
                                .environment(\.layoutDirection, .leftToRight)
                        }
                }
            }
        }
    }
}
