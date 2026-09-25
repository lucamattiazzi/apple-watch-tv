import Foundation
import AVFoundation
import CoreGraphics

struct VideoConverter {
    enum Failure: LocalizedError {
        case noVideo
        var errorDescription: String? { String(localized: "This video could not be read. Try another file.") }
    }
    static func convert(url: URL, title: String) async throws -> ImportedVideo {
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration).seconds
        guard duration.isFinite, duration > 0, !(try await asset.loadTracks(withMediaType: .video)).isEmpty else {
            throw Failure.noVideo
        }
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 960, height: 960)
        var frames: [[UInt8]] = []
        for second in 0..<30 {
            try Task.checkCancellation()
            let time = (Double(second) + 0.5).truncatingRemainder(dividingBy: min(duration, 30))
            let result = try await generator.image(at: CMTime(seconds: time, preferredTimescale: 600))
            var pixels = [UInt8](repeating: 0, count: 96 * 54)
            let image = result.image
            let scale = min(96 / CGFloat(image.width), 54 / CGFloat(image.height))
            let rect = CGRect(x: (96 - CGFloat(image.width) * scale) / 2,
                              y: (54 - CGFloat(image.height) * scale) / 2,
                              width: CGFloat(image.width) * scale, height: CGFloat(image.height) * scale)
            pixels.withUnsafeMutableBytes { bytes in
                let context = CGContext(data: bytes.baseAddress, width: 96, height: 54,
                    bitsPerComponent: 8, bytesPerRow: 96, space: CGColorSpaceCreateDeviceGray(),
                    bitmapInfo: CGImageAlphaInfo.none.rawValue)!
                context.interpolationQuality = .high
                context.draw(image, in: rect)
            }
            frames.append(pixels)
        }
        var histogram = [Int](repeating: 0, count: 256)
        for frame in frames { for value in frame { histogram[Int(value)] += 1 } }
        let total = 30 * 96 * 54
        func percentile(_ limit: Int) -> Int {
            var count = 0
            for i in 0..<256 { count += histogram[i]; if count > limit { return i } }
            return 255
        }
        var low = percentile(total * 2 / 100), high = percentile(total * 98 / 100)
        if high <= low { low = 0; high = 255 }
        let quantized = frames.map { frame in frame.map { value in
            UInt8(min(5, max(0, (Int(value) - low) * 6 / max(1, high - low + 1))))
        } }
        let id = UUID()
        let fonts = try ["Full", "Top", "Bottom"].map { part -> VideoFontAsset in
            guard let templateURL = Bundle.main.url(forResource: "Default" + part, withExtension: "ttf") else {
                throw ImportedVideo.Failure.invalidFont
            }
            let data = try VideoFontEncoder.encode(frames: quantized, part: part,
                template: Data(contentsOf: templateURL), family: ImportedVideo.family(id: id, part: part))
            return VideoFontAsset(part: part, data: data)
        }
        return ImportedVideo(id: id, title: String(title.prefix(200)), fonts: fonts)
    }
}
