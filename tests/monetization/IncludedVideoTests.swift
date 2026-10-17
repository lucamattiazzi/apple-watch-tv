import Foundation

@main
struct IncludedVideoTests {
    static func main() throws {
        precondition(IncludedVideo.allCases.map(\.rawValue) == ["naufrago", "orbita", "acquario", "ingranaggi", "labirinto"])
        let directory = URL(fileURLWithPath: CommandLine.arguments[1])
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let store = ImportedVideoStore(root: root)
        var ids = Set<UUID>()
        for included in IncludedVideo.allCases {
            for style in IncludedVideoStyle.allCases {
                let video = try included.load(style: style, directory: directory)
                precondition(video.title == included.title)
                precondition(IncludedVideo.contains(video))
                let oldID = UUID(uuidString: video.id.uuidString.replacingOccurrences(of: "9F300003", with: "9F300002"))!
                let old = ImportedVideo(version: video.version, id: oldID, title: video.title, fonts: [], frames: video.frames, playback: video.playback)
                let replacement = try IncludedVideo.refreshed(old, directory: directory)
                precondition(replacement?.id == video.id)
                precondition(included.isSelected(video, style: style))
                precondition(ids.insert(video.id).inserted)
                let frames = try video.renderWidgetFrames()
                precondition(frames.count == 60)
                precondition(frames.allSatisfy {
                    $0.width == (style == .bw ? 192 : 256) &&
                    $0.height == (style == .bw ? 108 : 144)
                })
                try store.install(video)
                try store.prepareWidgetAssets(video)
                let metadata = try store.widgetMetadata()!
                precondition(metadata.id == video.id)
                precondition(metadata.episodeCount == (included == .naufrago ? 12 : 1))
                for episode in 0..<video.episodeCount {
                    for part in ["Full", "Top", "Bottom"] {
                        let cached = try store.widgetFrames(metadata, part: part, episode: episode)
                        precondition(cached.count == 60)
                        precondition(cached[0].height ==
                            (part == "Full" ? frames[0].height : frames[0].height / 2))
                    }
                }
                print("PASS: \(included.title) \(style.rawValue) decode, install and widget cache")
            }
        }
        let custom = ImportedVideo(id: UUID(), title: "Custom", fonts: [])
        precondition(!IncludedVideo.contains(custom))
        let unchanged = try IncludedVideo.refreshed(custom, directory: directory)
        precondition(unchanged == nil)
    }
}
