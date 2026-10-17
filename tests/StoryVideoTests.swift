import Foundation

@main
struct StoryVideoTests {
    static func main() throws {
        let directory = URL(fileURLWithPath: CommandLine.arguments[1])
        let basic = try IncludedVideo.acquario.load(style: .bw, directory: directory)
        let root = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: root) }
        let store = ImportedVideoStore(root: root)
        let story = ImportedVideo(version: 3, id: UUID(), title: "Story", fonts: [],
            frames: Array(basic.frames!.prefix(30)) + Array(basic.frames!.prefix(30).reversed()))
        try story.validate()
        precondition(story.episodeCount == 2)
        try store.install(story)
        try store.prepareWidgetAssets(story)
        let metadata = try store.widgetMetadata()!
        precondition(metadata.frameCount == 60 && metadata.episodeCount == 2)
        precondition(metadata.episode(at: Date(timeIntervalSince1970: 899)) == 0)
        precondition(metadata.episode(at: Date(timeIntervalSince1970: 900)) == 1)
        precondition(metadata.episode(at: Date(timeIntervalSince1970: 1800)) == 0)
        precondition(metadata.episode(at: Date(timeIntervalSince1970: -1)) == 1)
        let second = try store.widgetFrames(metadata, part: "Full", episode: 1)
        let actual = try ImportedVideo.pngData(second[0])
        let expected = try ImportedVideo.pngData(story.renderWidgetFrames(episode: 1)[0])
        precondition(actual == expected)
        for count in [0, 29, 31, 390] {
            let invalid = ImportedVideo(version: 3, id: UUID(), title: "Bad", fonts: [],
                frames: Array(repeating: basic.frames![0], count: count))
            do { try invalid.validate(); fatalError("Accepted invalid story size") }
            catch ImportedVideo.Failure.invalidPackage {}
        }
        do { _ = try store.widgetFrames(metadata, part: "Full", episode: 2); fatalError("Out of bounds episode") }
        catch ImportedVideo.Failure.invalidPackage {}
        try store.install(basic)
        try store.prepareWidgetAssets(basic)
        let basicMetadata = try store.widgetMetadata()!
        let basicFrames = try store.widgetFrames(basicMetadata, part: "Full")
        precondition(basicMetadata.frameCount == basic.totalFrameCount && basicFrames.count == basic.timing.framesPerEpisode)
        print("PASS: story validation, second-episode cache, bounds, and ordinary video replacement")
    }
}
