import SwiftUI

/// AniWeather's opaque frame stack, extended to one-minute videos and synchronized halves.
/// Timer texts may update late: the previous opaque frame and the frame-zero backstop
/// prevent gaps. The last second has its own group so it cannot cover the next loop.
struct StackedVideo {
    let frames: [CGImage]
    let timing: VideoPlayback
    let part: VideoPart
    var fontName: String { "TVWatchGate\(timing.duration)" + (part == .full ? "" : "Half") + "-Regular" }
    var main: ClosedRange<Int> { 0...((timing.duration - 1) * timing.framesPerSecond) }
    var wrap: Range<Int> { ((timing.duration - 1) * timing.framesPerSecond + 1)..<frames.count }
    var wrapStart: TimeInterval { Double(timing.duration - 1) }

    /// The cache reader supplies only the requested half, avoiding a second full-frame array.
    init?(frames: [CGImage], timing: VideoPlayback, part: VideoPart = .full) {
        guard timing.isValid, frames.count == timing.framesPerEpisode, let first = frames.first,
              first.width * 9 == first.height * (part == .full ? 16 : 32),
              frames.allSatisfy({ $0.width == first.width && $0.height == first.height }) else { return nil }
        self.timing = timing
        self.part = part
        self.frames = frames
    }
    func start(of index: Int) -> TimeInterval { Double(index) / Double(timing.framesPerSecond) }
}

struct StackedVideoView: View {
    let video: StackedVideo
    let referenceDate: Date
    var body: some View {
        let anchor = Calendar.current.startOfDay(for: referenceDate).addingTimeInterval(-Double(video.timing.duration))
        StackedFramesView(video: video) { Text(anchor.addingTimeInterval($0), style: .timer) }
    }
}

struct StackedFramesView: View {
    let video: StackedVideo
    let clock: (TimeInterval) -> Text
    var body: some View {
        GeometryReader { geometry in
            let size = min(geometry.size.width / 96, geometry.size.height / video.part.rows) * 64
            ZStack(alignment: video.part.alignment) {
                Color.black
                frame(0)
                ForEach(Array(video.main), id: \.self) { gated($0, size: size) }
                ZStack(alignment: video.part.alignment) {
                    ForEach(Array(video.wrap), id: \.self) { gated($0, size: size) }
                }
                .mask { gate(video.wrapStart, size: size) }
            }
        }
    }
    private func frame(_ index: Int) -> some View {
        Image(decorative: video.frames[index], scale: 1).resizable().interpolation(.none).scaledToFit()
    }
    private func gated(_ index: Int, size: CGFloat) -> some View {
        frame(index).mask { gate(video.start(of: index), size: size) }
    }
    private func gate(_ offset: TimeInterval, size: CGFloat) -> some View {
        clock(offset)
            .font(.custom(video.fontName, fixedSize: size))
            .foregroundStyle(.white)
            .lineLimit(1)
            .environment(\.locale, Locale(identifier: "en_US_POSIX"))
            .environment(\.layoutDirection, .leftToRight)
    }
}
