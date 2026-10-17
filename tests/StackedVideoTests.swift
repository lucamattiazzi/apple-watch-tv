import SwiftUI
import CoreText

func solidFrames(_ count: Int) -> [CGImage] {
    (0..<count).map { index in
        var bytes = [UInt8](repeating: 0, count: 192 * 108 * 4)
        for y in 0..<108 {
            for x in 0..<192 {
                let offset = (y * 192 + x) * 4
                bytes[offset] = UInt8(32 + index % 8 * 26)
                bytes[offset + 1] = UInt8(32 + index / 8 * 13)
                bytes[offset + 2] = y < 54 ? 64 : 192
                bytes[offset + 3] = 255
            }
        }
        return CGImage(width: 192, height: 108, bitsPerComponent: 8, bitsPerPixel: 32,
            bytesPerRow: 192 * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
            bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue),
            provider: CGDataProvider(data: Data(bytes) as CFData)!, decode: nil,
            shouldInterpolate: false, intent: .defaultIntent)!
    }
}

func pixel(_ image: CGImage, x: Int? = nil, y: Int? = nil) -> [UInt8] {
    let w = image.width, h = image.height
    var data = [UInt8](repeating: 0, count: w * h * 4)
    data.withUnsafeMutableBytes {
        let context = CGContext(data: $0.baseAddress, width: w, height: h, bitsPerComponent: 8,
            bytesPerRow: w * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
        context.draw(image, in: CGRect(x: 0, y: 0, width: w, height: h))
    }
    let index = ((y ?? h / 2) * w + (x ?? w / 2)) * 4
    return Array(data[index..<index + 3])
}
@MainActor func visible(_ video: StackedVideo, at time: Double, late: Set<Double> = [], hours: Int = 0) -> Int? {
    let view = StackedFramesView(video: video) { offset in
        let elapsed = Double(video.timing.duration * 2 + hours * 3600) + time - offset - (late.contains(offset) ? 0.1 : 0)
        let seconds = Int(elapsed.rounded(.down))
        return Text(verbatim: hours > 0
            ? String(format: "%d:%02d:%02d", seconds / 3600, seconds / 60 % 60, seconds % 60)
            : String(format: "%d:%02d", seconds / 60, seconds % 60))
    }
    let renderer = ImageRenderer(content: view.frame(width: 160, height: video.part == .full ? 90 : 45))
    renderer.scale = 1
    let color = pixel(renderer.cgImage!)

    return video.frames.firstIndex { zip(pixel($0), color).allSatisfy { abs(Int($0) - Int($1)) <= 2 } }
}
@main struct StackedVideoTests {
    @MainActor static func main() {
        for period in [30, 60] {
            for half in ["", "Half"] {
                let url = URL(fileURLWithPath: "WatchTV/Shared/TimerFonts/TVWatchGate\(period)\(half).ttf")
                precondition(CTFontManagerRegisterFontsForURL(url as CFURL, .process, nil))
            }
        }
        for duration in [30, 60] {
            let timing = VideoPlayback(framesPerSecond: 2, duration: duration)
            let frames = solidFrames(timing.framesPerEpisode)
            for part in VideoPart.allCases {
                let prepared = part == .full ? frames : frames.map {
                    $0.cropping(to: CGRect(x: 0, y: part == .top ? 0 : 54, width: 192, height: 54))!
                }
                let video = StackedVideo(frames: prepared, timing: timing, part: part)!
                for time in stride(from: 0.05, to: Double(duration), by: 0.25) {
                    precondition(visible(video, at: time) == Int(time * 2), "Wrong frame: \(duration)s \(part) at \(time)")
                }
                for k in [1, 17, (duration - 1) * 2, timing.framesPerEpisode - 1] {
                    precondition(visible(video, at: Double(k) / 2 + 0.05, late: [video.start(of: k)]) == k - 1)
                }
                precondition(visible(video, at: 0.05, late: [0]) == 0)
                precondition(visible(video, at: 0.05, late: [video.wrapStart]) == timing.framesPerEpisode - 1)
                precondition(visible(video, at: Double(duration) - 0.45, hours: 11) == timing.framesPerEpisode - 1)
                print("PASS: \(duration)s \(part), every half-second, delayed timers, hour prefix and wrap")
            }
        }
        let wrongCount = StackedVideo(frames: solidFrames(30), timing: VideoPlayback(framesPerSecond: 2, duration: 60))
        precondition(wrongCount == nil)
    }
}
