import SwiftUI
import WidgetKit
import VideoWidgetLibrary

private struct PersonalVideoEntry: TimelineEntry {
    let date: Date
    var video: WidgetVideo?
    var usesBundledVideo = false
    var message = String(localized: "Send a video from TV Watch on your iPhone")
    var anchor: Date { Calendar.current.startOfDay(for: date).addingTimeInterval(-30) }
}

private struct PersonalVideoProvider: TimelineProvider {
    let part: VideoPart

    func placeholder(in context: Context) -> PersonalVideoEntry {
        PersonalVideoEntry(date: .now, usesBundledVideo: true)
    }
    private func entry() -> PersonalVideoEntry {
        var entry = PersonalVideoEntry(date: .now)
        guard let store = ImportedVideoStore.shared else {
            entry.message = String(localized: "Shared storage is unavailable")
            return entry
        }
        do {
            guard let metadata = try store.widgetMetadata() else {
                entry.usesBundledVideo = true
                return entry
            }
            guard metadata.frameCount == 30 else {
                entry.message = String(localized: "Open TV Watch on your Watch to prepare the frames")
                return entry
            }
            let frames = try store.widgetFrames(metadata, part: "Full")
            let videoPart: VideoWidgetLibrary.VideoPart
            switch part {
            case .full: videoPart = .full
            case .top: videoPart = .top
            case .bottom: videoPart = .bottom
            }
            entry.video = try WidgetVideo(frames: frames, part: videoPart)
        } catch { entry.message = error.localizedDescription }
        return entry
    }
    func getSnapshot(in context: Context, completion: @escaping (PersonalVideoEntry) -> Void) {
        completion(entry())
    }
    func getTimeline(in context: Context, completion: @escaping (Timeline<PersonalVideoEntry>) -> Void) {
        completion(Timeline(entries: [entry()], policy: .never))
    }
}

private struct PersonalVideoEntryView: View {
    let entry: PersonalVideoEntry
    let part: VideoPart
    var body: some View {
        if entry.usesBundledVideo {
            VideoView(text: Text(entry.anchor, style: .timer), part: part)
        } else if let video = entry.video {
            WidgetVideoView(video: video, referenceDate: entry.date)
        } else {
            Text(entry.message).font(.caption2).multilineTextAlignment(.center)
        }
    }
}

private func personalConfiguration(kind: String, title: LocalizedStringKey, part: VideoPart) -> some WidgetConfiguration {
    StaticConfiguration(kind: kind, provider: PersonalVideoProvider(part: part)) { entry in
        PersonalVideoEntryView(entry: entry, part: part)
            .containerBackground(.black, for: .widget)
    }
    .configurationDisplayName(title)
    .description("Your active video: an included animation or your own video from iPhone. 30 seconds at 1 fps.")
    .supportedFamilies([.accessoryRectangular])
    .contentMarginsDisabled()
}

struct PersonalVideoWidget: Widget {
    var body: some WidgetConfiguration {
        personalConfiguration(kind: "TVPersonalFull", title: "TV Watch · Full video", part: .full)
    }
}
struct PersonalVideoTopWidget: Widget {
    var body: some WidgetConfiguration {
        personalConfiguration(kind: "TVPersonalTop", title: "TV Watch · Top video", part: .top)
    }
}
struct PersonalVideoBottomWidget: Widget {
    var body: some WidgetConfiguration {
        personalConfiguration(kind: "TVPersonalBottom", title: "TV Watch · Bottom video", part: .bottom)
    }
}
