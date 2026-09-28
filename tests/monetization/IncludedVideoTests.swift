import Foundation

@main
struct IncludedVideoTests {
    static func main() throws {
        let directory = URL(fileURLWithPath: CommandLine.arguments[1])
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let store = ImportedVideoStore(root: root)
        var ids = Set<UUID>()
        for included in IncludedVideo.allCases {
            let video = try included.load(directory: directory)
            precondition(video.title == included.title)
            precondition(IncludedVideo.contains(video))
            precondition(ids.insert(video.id).inserted)
            let frames = try video.renderWidgetFrames()
            precondition(frames.count == 30)
            precondition(frames.allSatisfy { $0.width == 192 && $0.height == 108 })
            try store.install(video)
            try store.prepareWidgetAssets(video)
            let metadata = try store.widgetMetadata()!
            precondition(metadata.id == video.id)
            for part in ["Full", "Top", "Bottom"] {
                let cached = try store.widgetFrames(metadata, part: part)
                precondition(cached.count == 30)
                precondition(cached[0].height == (part == "Full" ? 108 : 54))
            }
            print("PASS: \(included.title) decode, install, selection and full/split widget cache")
        }
        let custom = ImportedVideo(id: UUID(), title: "Custom", fonts: [])
        precondition(!IncludedVideo.contains(custom))
    }
}
