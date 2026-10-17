import Foundation
import CoreGraphics

@main struct MinuteConversionTests {
    static func rgb(_ image: CGImage) -> [UInt8] {
        var bytes = [UInt8](repeating: 0, count: image.width * image.height * 4)
        bytes.withUnsafeMutableBytes {
            let context = CGContext(data: $0.baseAddress, width: image.width, height: image.height,
                bitsPerComponent: 8, bytesPerRow: image.width * 4, space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
            context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
        }
        let center = (image.height / 2 * image.width + image.width / 2) * 4
        return Array(bytes[center..<center + 3])
    }
    static func main() async throws {
        // 65 seconds: red 0–30, green 30–59, blue 59–60, yellow after the cutoff.
        let video = try await VideoConverter.convert(url: URL(fileURLWithPath: CommandLine.arguments[1]),
            title: "Minute fixture", mode: .color)
        precondition(video.frames?.count == 120 && video.timing.duration == 60 && video.episodeCount == 1)
        let frames = try video.renderWidgetFrames()
        let start = rgb(frames[0]), secondHalf = rgb(frames[60]), last = rgb(frames[119])
        precondition(start[0] > 200 && start[1] < 40 && start[2] < 40)
        precondition(secondHalf[1] > 80 && secondHalf[0] < 40 && secondHalf[2] < 40,
                     "Seconds after 30 must be preserved")
        precondition(last[2] > 200 && last[0] < 40 && last[1] < 40,
                     "Keep the last half-second; exclude content after 60 seconds")
        print("PASS: real 65-second AVFoundation source, second half retained, 60-second cutoff, 120 frames")
    }
}
