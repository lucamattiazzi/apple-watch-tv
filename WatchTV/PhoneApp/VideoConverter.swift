import Foundation
import AVFoundation
import CoreGraphics

enum VideoConversionMode: String, CaseIterable {
    case seiko, color

    var width: Int { self == .seiko ? 128 : 256 }
    var height: Int { self == .seiko ? 72 : 144 }
}

struct VideoConverter {
    enum Failure: LocalizedError {
        case noVideo
        var errorDescription: String? { String(localized: "This video could not be read. Try another file.") }
    }
    static func convert(url: URL, title: String, mode: VideoConversionMode = .seiko) async throws -> ImportedVideo {
        let asset = AVURLAsset(url: url)
        let duration = try await asset.load(.duration).seconds
        guard duration.isFinite, duration > 0, !(try await asset.loadTracks(withMediaType: .video)).isEmpty else {
            throw Failure.noVideo
        }
        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.maximumSize = CGSize(width: 960, height: 960)
        generator.requestedTimeToleranceBefore = .zero
        generator.requestedTimeToleranceAfter = .zero
        let width = mode.width, height = mode.height
        let channels = mode == .seiko ? 1 : 4
        let space = mode == .seiko ? CGColorSpaceCreateDeviceGray() : CGColorSpace(name: CGColorSpace.sRGB)!
        let bitmapInfo = mode == .seiko ? CGImageAlphaInfo.none.rawValue : CGImageAlphaInfo.premultipliedLast.rawValue
        var frames: [[UInt8]] = []
        for second in 0..<30 {
            try Task.checkCancellation()
            let time = (Double(second) + 0.5).truncatingRemainder(dividingBy: min(duration, 30))
            let result = try await generator.image(at: CMTime(seconds: time, preferredTimescale: 600))
            let image = result.image
            var pixels = [UInt8](repeating: 0, count: width * height * channels)
            let scale = min(CGFloat(width) / CGFloat(image.width), CGFloat(height) / CGFloat(image.height))
            let rect = CGRect(x: (CGFloat(width) - CGFloat(image.width) * scale) / 2,
                              y: (CGFloat(height) - CGFloat(image.height) * scale) / 2,
                              width: CGFloat(image.width) * scale, height: CGFloat(image.height) * scale)
            try pixels.withUnsafeMutableBytes { bytes in
                guard let context = CGContext(data: bytes.baseAddress, width: width, height: height,
                    bitsPerComponent: 8, bytesPerRow: width * channels, space: space,
                    bitmapInfo: bitmapInfo) else { throw Failure.noVideo }
                context.setFillColor(CGColor(gray: 0, alpha: 1))
                context.fill(CGRect(x: 0, y: 0, width: width, height: height))
                context.interpolationQuality = .high
                context.draw(image, in: rect)
            }
            frames.append(pixels)
        }
        if mode == .seiko {
            var histogram = [Int](repeating: 0, count: 256)
            for frame in frames { for value in frame { histogram[Int(value)] += 1 } }
            let total = frames.count * width * height
            func percentile(_ limit: Int) -> Int {
                var count = 0
                for i in 0..<256 { count += histogram[i]; if count > limit { return i } }
                return 255
            }
            var low = percentile(total * 2 / 100), high = percentile(total * 98 / 100)
            if high <= low { low = 0; high = 255 }
            frames = frames.map { frame in frame.map { value in
                let level = min(7, max(0, (Int(value) - low) * 8 / (high - low + 1)))
                return UInt8(level * 255 / 7)
            } }
        }
        let pngs = try frames.map { pixels -> Data in
            guard let provider = CGDataProvider(data: Data(pixels) as CFData),
                  let image = CGImage(width: width, height: height, bitsPerComponent: 8,
                    bitsPerPixel: channels * 8, bytesPerRow: width * channels, space: space,
                    bitmapInfo: CGBitmapInfo(rawValue: bitmapInfo), provider: provider,
                    decode: nil, shouldInterpolate: false, intent: .defaultIntent) else { throw Failure.noVideo }
            return try ImportedVideo.pngData(image)
        }
        let video = ImportedVideo(version: 2, id: UUID(), title: String(title.prefix(200)), fonts: [], frames: pngs)
        try video.validate()
        return video
    }
}
