import Foundation

enum IncludedVideoStyle: String, CaseIterable {
    case bw, color
}

/// Stable identifiers keep bundled choices distinct from imported movies.
enum IncludedVideo: String, CaseIterable, Identifiable {
    case naufrago, orbita, acquario, ingranaggi, labirinto
    var id: String { rawValue }
    var title: String {
        switch self {
        case .orbita: return "Orbita"
        case .ingranaggi: return "Ingranaggi"
        case .acquario: return "Acquario"
        case .naufrago: return "Isola deserta"
        case .labirinto: return "Labirinto 3D"
        }
    }
    func videoID(style: IncludedVideoStyle) -> UUID {
        let firstIndex: Int
        switch self {
        case .orbita: firstIndex = 3
        case .ingranaggi: firstIndex = 7
        case .acquario: firstIndex = 5
        case .naufrago: firstIndex = 1
        case .labirinto: firstIndex = 9
        }
        let index = firstIndex + (style == .color ? 1 : 0)
        return UUID(uuidString: String(format: "9F300003-0000-4000-8000-%012d", index))!
    }
    func isSelected(_ video: ImportedVideo?, style: IncludedVideoStyle) -> Bool {
        guard let video else { return false }
        return video.id == videoID(style: style) ||
            (self == .orbita && style == .bw && video.id == ImportedVideo.bundledID)
    }
    func load(style: IncludedVideoStyle, directory: URL = Bundle.main.resourceURL!) throws -> ImportedVideo {
        let url = directory.appendingPathComponent("IncludedVideos")
            .appendingPathComponent(rawValue + "-" + style.rawValue + ".video")
        let video = try PropertyListDecoder().decode(ImportedVideo.self, from: Data(contentsOf: url))
        guard video.id == videoID(style: style) else { throw ImportedVideo.Failure.invalidPackage }
        try video.validate()
        return video
    }
    /// Upgrade shipped stock artwork while preserving every personal import.
    static func refreshed(_ video: ImportedVideo, directory: URL = Bundle.main.resourceURL!) throws -> ImportedVideo? {
        if video.id == ImportedVideo.bundledID { return try orbita.load(style: .bw, directory: directory) }
        for included in allCases {
            for style in IncludedVideoStyle.allCases {
                let current = included.videoID(style: style).uuidString
                let previousIDs = ["9F300001", "9F300002"].map {
                    current.replacingOccurrences(of: "9F300003", with: $0)
                }
                if previousIDs.contains(video.id.uuidString) { return try included.load(style: style, directory: directory) }
            }
        }
        return nil
    }
    static func contains(_ video: ImportedVideo) -> Bool {
        video.id == ImportedVideo.bundledID ||
            allCases.contains { included in
                IncludedVideoStyle.allCases.contains { included.videoID(style: $0) == video.id }
            }
    }
}
