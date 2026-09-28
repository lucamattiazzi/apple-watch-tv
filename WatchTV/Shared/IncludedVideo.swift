import Foundation

/// Stable identifiers keep bundled choices distinct from imported movies.
enum IncludedVideo: String, CaseIterable, Identifiable {
    case orbita, eclisse, cometa, pulsar, vortice
    var id: String { rawValue }
    var title: String { rawValue.capitalized }
    var videoID: UUID {
        switch self {
        case .orbita: return ImportedVideo.bundledID
        case .eclisse: return UUID(uuidString: "9F280001-0000-4000-8000-000000000001")!
        case .cometa: return UUID(uuidString: "9F280001-0000-4000-8000-000000000002")!
        case .pulsar: return UUID(uuidString: "9F280001-0000-4000-8000-000000000003")!
        case .vortice: return UUID(uuidString: "9F280001-0000-4000-8000-000000000004")!
        }
    }
    func load(directory: URL = Bundle.main.resourceURL!) throws -> ImportedVideo {
        if self == .orbita { return try ImportedVideo.bundled(directory: directory) }
        let url = directory.appendingPathComponent("IncludedVideos").appendingPathComponent(rawValue + ".video")
        let video = try PropertyListDecoder().decode(ImportedVideo.self, from: Data(contentsOf: url))
        guard video.id == videoID else { throw ImportedVideo.Failure.invalidPackage }
        try video.validate()
        return video
    }
    static func contains(_ video: ImportedVideo) -> Bool {
        allCases.contains { $0.videoID == video.id }
    }
}
