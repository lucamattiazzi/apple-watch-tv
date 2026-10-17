import Foundation

@main
struct VideoPlaybackTests {
    static func main() throws {
        let stock = try IncludedVideo.acquario.load(style: .bw, directory: URL(fileURLWithPath: "WatchTV/Shared"))
        let png = stock.frames![0]
        var video = ImportedVideo(version: 4, id: UUID(), title: "One minute", fonts: [],
            frames: Array(repeating: png, count: 120), playback: VideoPlayback(framesPerSecond: 2, duration: 60))
        try video.validate()
        precondition(video.episodeCount == 1 && video.timing.framesPerEpisode == 120)
        let decoded = try PropertyListDecoder().decode(ImportedVideo.self, from: video.encoded())
        precondition(decoded.timing == video.timing)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let store = ImportedVideoStore(root: root)
        try store.install(decoded)
        try store.prepareWidgetAssets(decoded)
        let metadata = try store.widgetMetadata()!
        precondition(metadata.episodeCount == 1 && metadata.timing.duration == 60)
        let frames = try store.widgetFrames(metadata, part: "Full")
        precondition(frames.count == 120)
        for count in [0, 30, 60, 119, 121, 1560] {
            video.frames = Array(repeating: png, count: count)
            do { try video.validate(); fatalError("Accepted incomplete minute") }
            catch ImportedVideo.Failure.invalidPackage {}
        }
        video.frames = Array(repeating: png, count: 120)
        for timing in [VideoPlayback(framesPerSecond: 0, duration: 60),
                       VideoPlayback(framesPerSecond: 2, duration: 61),
                       VideoPlayback(framesPerSecond: 3, duration: 30)] {
            video.playback = timing
            do { try video.validate(); fatalError("Accepted invalid timing") }
            catch ImportedVideo.Failure.invalidPackage {}
        }
        // Old packages and metadata have no playback key and still mean 30-frame episodes.
        let legacy = ImportedVideo(version: 3, id: UUID(), title: "Old story", fonts: [],
            frames: Array(repeating: png, count: 120))
        let restored = try PropertyListDecoder().decode(ImportedVideo.self, from: legacy.encoded())
        try restored.validate()
        precondition(restored.timing == .legacy && restored.episodeCount == 4)
        let oldMetadata = try JSONDecoder().decode(WidgetVideoMetadata.self,
            from: Data("{\"id\":\"\(legacy.id)\",\"title\":\"Old\",\"frameCount\":120}".utf8))
        precondition(oldMetadata.episodeCount == 4 && oldMetadata.timing == .legacy)
        print("PASS: 60 seconds at 2 fps, cache timing, invalid counts/rates, old-package compatibility")
    }
}
