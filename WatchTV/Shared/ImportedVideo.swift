import Foundation
import CoreText
import ImageIO

struct VideoFontAsset: Codable {
    let part: String
    let data: Data
}

struct ImportedVideo: Codable {
    static let bundledID = UUID(uuidString: "3FB9A59E-9076-45D4-AF77-C80422A1A2C0")!
    var version = 1
    let id: UUID
    let title: String
    let fonts: [VideoFontAsset]
    var frames: [Data]? = nil

    enum Failure: LocalizedError {
        case invalidPackage, unavailableStorage, invalidFont
        var errorDescription: String? {
            switch self {
            case .invalidPackage: return String(localized: "The converted video is incomplete or invalid.")
            case .unavailableStorage: return String(localized: "Shared storage on your Watch is unavailable.")
            case .invalidFont: return String(localized: "The converted video could not be opened.")
            }
        }
    }
    static func family(id: UUID, part: String) -> String {
        id == bundledID ? "Default" + part : "Personal" + id.uuidString.replacingOccurrences(of: "-", with: "") + part
    }
    static func bundled(directory: URL = Bundle.main.resourceURL!) throws -> ImportedVideo {
        let fonts = try ["Full", "Top", "Bottom"].map { part in
            VideoFontAsset(part: part, data: try Data(contentsOf:
                directory.appendingPathComponent("Default" + part + ".ttf")))
        }
        return ImportedVideo(id: bundledID, title: "Orbita", fonts: fonts)
    }
    func encoded() throws -> Data {
        let encoder = PropertyListEncoder()
        encoder.outputFormat = .binary
        return try encoder.encode(self)
    }
    // Used inside the app to rasterize imported frames before widget delivery.
    func font(part: String, size: CGFloat = 64) throws -> CTFont {
        guard ["Full", "Top", "Bottom"].contains(part),
              let asset = fonts.first(where: { $0.part == part }),
              let descriptor = CTFontManagerCreateFontDescriptorFromData(asset.data as CFData) else {
            throw Failure.invalidFont
        }
        let font = CTFontCreateWithFontDescriptor(descriptor, size, nil)
        guard CTFontCopyPostScriptName(font) as String == Self.family(id: id, part: part) + "-Regular" else {
            throw Failure.invalidFont
        }
        return font
    }

    static func pngData(_ image: CGImage) throws -> Data {
        let png = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(png, "public.png" as CFString, 1, nil) else {
            throw Failure.invalidPackage
        }
        CGImageDestinationAddImage(destination, image, nil)
        guard CGImageDestinationFinalize(destination) else { throw Failure.invalidPackage }
        return png as Data
    }
    static func decodeFrame(_ data: Data) throws -> CGImage {
        guard data.count <= 256_000,
              let source = CGImageSourceCreateWithData(data as CFData, nil),
              CGImageSourceGetType(source) as String? == "public.png",
              CGImageSourceGetCount(source) == 1,
              let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
              let width = properties[kCGImagePropertyPixelWidth] as? Int,
              let height = properties[kCGImagePropertyPixelHeight] as? Int,
              [(128, 72), (192, 108), (256, 144)].contains(where: { $0 == width && $1 == height }),
              let image = CGImageSourceCreateImageAtIndex(source, 0,
                [kCGImageSourceShouldCacheImmediately: true] as CFDictionary) else { throw Failure.invalidPackage }
        return image
    }
    func renderWidgetFrames() throws -> [CGImage] {
        if version == 2 {
            guard let frames, frames.count == 30 else { throw Failure.invalidPackage }
            return try frames.map(Self.decodeFrame)
        }
        let font = try font(part: "Full", size: 128)
        return try (0..<30).map { try Self.rasterFrame(font: font, height: 108, second: $0) }
    }
    private static func rasterFrame(font: CTFont, height: Int, second: Int) throws -> CGImage {
        guard let context = CGContext(data: nil, width: 192, height: height,
            bitsPerComponent: 8, bytesPerRow: 192, space: CGColorSpaceCreateDeviceGray(),
            bitmapInfo: CGImageAlphaInfo.none.rawValue) else { throw Failure.invalidFont }
        context.setFillColor(CGColor(gray: 0, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: 192, height: height))
        let line = CTLineCreateWithAttributedString(NSAttributedString(string: String(format: "0:%02d", second), attributes: [
            NSAttributedString.Key(kCTFontAttributeName as String): font,
            NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 1, alpha: 1)
        ]))
        context.textPosition = .zero
        CTLineDraw(line, context)
        guard let image = context.makeImage() else { throw Failure.invalidFont }
        return image
    }

    func validate() throws {
        guard title.count <= 200 else { throw Failure.invalidPackage }
        if version == 2 {
            guard fonts.isEmpty, let frames, frames.count == 30 else { throw Failure.invalidPackage }
            var dimensions: CGSize?
            for data in frames {
                let image = try Self.decodeFrame(data)
                let size = CGSize(width: image.width, height: image.height)
                if let dimensions, size != dimensions { throw Failure.invalidPackage }
                dimensions = size
            }
            return
        }
        guard version == 1, frames == nil, fonts.count == 3,
              Set(fonts.map(\.part)) == Set(["Full", "Top", "Bottom"]) else {
            throw Failure.invalidPackage
        }
        for font in fonts {
            guard font.data.count < 8_000_000,
                  let provider = CGDataProvider(data: font.data as CFData),
                  let cgFont = CGFont(provider),
                  cgFont.postScriptName as String? == Self.family(id: id, part: font.part) + "-Regular" else {
                throw Failure.invalidFont
            }
        }
    }
}

struct WidgetVideoMetadata: Codable {
    let id: UUID
    let title: String
    var frameCount: Int? = nil
}

struct ImportedVideoStore {
    // Serialize imports and cache publication so an older job cannot replace a newer video.
    private static let writeLock = NSLock()
    let root: URL
    static var shared: ImportedVideoStore? {
        FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: "group.com.tvwatch.fonthack.video")
            .map { ImportedVideoStore(root: $0.appendingPathComponent("ImportedVideos")) }
    }
    func current() -> ImportedVideo? {
        guard let data = try? Data(contentsOf: root.appendingPathComponent("current.video")) else { return nil }
        return try? PropertyListDecoder().decode(ImportedVideo.self, from: data)
    }
    func loadInitialVideo(bundledDirectory: URL = Bundle.main.resourceURL!) throws -> ImportedVideo {
        Self.writeLock.lock()
        let existing = current()
        if let existing {
            let displayedID = (try? widgetMetadata())?.id
            removePreviousVideos(keeping: Set([existing.id, displayedID].compactMap { $0 }))
        }
        Self.writeLock.unlock()
        if let existing { return existing }
        let video = try ImportedVideo.bundled(directory: bundledDirectory)
        try install(video)
        return video
    }
    // Prepared by the app, never by a widget provider. Legacy imports migrate
    // on the next app launch without sending the video again.
    func prepareWidgetAssets(_ video: ImportedVideo) throws {
        Self.writeLock.lock()
        defer { Self.writeLock.unlock() }
        if let current = current(), current.id != video.id { return }
        let directory = root.appendingPathComponent(video.id.uuidString)
        let framesDirectory = directory.appendingPathComponent("frames")
        let urls = (0..<30).map { framesDirectory.appendingPathComponent(String(format: "%02d.png", $0)) }
        let existing = try? widgetMetadata()
        if existing?.id == video.id, existing?.frameCount == 30,
           urls.allSatisfy({ FileManager.default.fileExists(atPath: $0.path) }) {
            removePreviousVideos(keeping: [video.id])
            return
        }
        try FileManager.default.createDirectory(at: framesDirectory, withIntermediateDirectories: true)
        let frames = try video.frames ?? video.renderWidgetFrames().map(ImportedVideo.pngData)
        for (index, png) in frames.enumerated() {
            try png.write(to: urls[index], options: .atomic)
        }
        // Publish only after every frame is ready; legacy metadata remains readable.
        let metadata = WidgetVideoMetadata(id: video.id, title: video.title, frameCount: 30)
        try JSONEncoder().encode(metadata).write(to: root.appendingPathComponent("current.widget"), options: .atomic)
        removePreviousVideos(keeping: [video.id])
    }
    func widgetFrames(_ metadata: WidgetVideoMetadata, part: String) throws -> [CGImage] {
        guard metadata.frameCount == 30, ["Full", "Top", "Bottom"].contains(part) else {
            throw ImportedVideo.Failure.invalidPackage
        }
        let directory = root.appendingPathComponent(metadata.id.uuidString).appendingPathComponent("frames")
        return try (0..<30).map { index in
            let url = directory.appendingPathComponent(String(format: "%02d.png", index))
            let image = try ImportedVideo.decodeFrame(Data(contentsOf: url))
            if part == "Full" { return image }
            let halfHeight = image.height / 2
            guard let half = image.cropping(to: CGRect(x: 0, y: part == "Top" ? 0 : halfHeight,
                                                       width: image.width, height: halfHeight)) else {
                throw ImportedVideo.Failure.invalidPackage
            }
            return half
        }
    }
    func widgetMetadata() throws -> WidgetVideoMetadata? {
        let url = root.appendingPathComponent("current.widget")
        guard FileManager.default.fileExists(atPath: url.path) else { return nil }
        return try JSONDecoder().decode(WidgetVideoMetadata.self, from: Data(contentsOf: url))
    }
    func install(_ video: ImportedVideo) throws {
        Self.writeLock.lock()
        defer { Self.writeLock.unlock() }
        try video.validate()
        let directory = root.appendingPathComponent(video.id.uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        for font in video.fonts {
            try font.data.write(to: directory.appendingPathComponent(font.part + ".ttf"), options: .atomic)
        }
        // Publish only once the package has been validated and any legacy fonts are ready.
        for font in video.fonts { _ = try registeredFont(video, part: font.part) }
        try video.encoded().write(to: root.appendingPathComponent("current.video"), options: .atomic)
        // Keep the previous widget cache only until the replacement cache is ready.
        let displayedID = (try? widgetMetadata())?.id
        removePreviousVideos(keeping: Set([video.id, displayedID].compactMap { $0 }))
    }
    private func removePreviousVideos(keeping ids: Set<UUID>) {
        let directories = (try? FileManager.default.contentsOfDirectory(at: root,
            includingPropertiesForKeys: [.isDirectoryKey])) ?? []
        for directory in directories {
            guard let id = UUID(uuidString: directory.lastPathComponent), !ids.contains(id),
                  (try? directory.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) == true else { continue }
            for part in ["Full", "Top", "Bottom"] {
                CTFontManagerUnregisterFontsForURL(directory.appendingPathComponent(part + ".ttf") as CFURL, .process, nil)
            }
            try? FileManager.default.removeItem(at: directory)
        }
    }
    func registeredFont(_ video: ImportedVideo, part: String, size: CGFloat = 64) throws -> CTFont {
        guard ["Full", "Top", "Bottom"].contains(part) else { throw ImportedVideo.Failure.invalidFont }
        // UIAppFonts already registers Orbita; watchOS rejects registering a second copy.
        if video.id == ImportedVideo.bundledID { return try video.font(part: part, size: size) }
        let url = root.appendingPathComponent(video.id.uuidString).appendingPathComponent(part + ".ttf")
        var error: Unmanaged<CFError>?
        if !CTFontManagerRegisterFontsForURL(url as CFURL, .process, &error) {
            let value = error?.takeRetainedValue()
            guard value.map({ CFErrorGetCode($0) == CTFontManagerError.alreadyRegistered.rawValue }) == true else {
                throw ImportedVideo.Failure.invalidFont
            }
        }
        let name = ImportedVideo.family(id: video.id, part: part) + "-Regular"
        let descriptor = CTFontDescriptorCreateWithAttributes([
            kCTFontNameAttribute: name, kCTFontURLAttribute: url
        ] as CFDictionary)
        let font = CTFontCreateWithFontDescriptor(descriptor, size, nil)
        guard CTFontCopyPostScriptName(font) as String == name else { throw ImportedVideo.Failure.invalidFont }
        return font
    }
}
