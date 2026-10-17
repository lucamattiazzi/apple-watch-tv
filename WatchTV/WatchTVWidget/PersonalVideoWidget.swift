import SwiftUI
import WidgetKit
import VideoWidgetLibrary

private struct PersonalVideoEntry: TimelineEntry {
    let date: Date
    var video: WidgetVideo?
    var stacked: StackedVideo?
    var usesBundledVideo = false
    var episodeCount = 1
    var message = String(localized: "Send a video from TV Watch on your iPhone")
    var anchor: Date { Calendar.current.startOfDay(for: date).addingTimeInterval(-30) }
}

private struct PersonalVideoProvider: TimelineProvider {
    let part: VideoPart

    func placeholder(in context: Context) -> PersonalVideoEntry {
        PersonalVideoEntry(date: .now, usesBundledVideo: true)
    }
    private func entry(at date: Date = .now) -> PersonalVideoEntry {
        var entry = PersonalVideoEntry(date: date)
        guard let store = ImportedVideoStore.shared else {
            entry.message = String(localized: "Shared storage is unavailable")
            return entry
        }
        do {
            guard let metadata = try store.widgetMetadata() else {
                entry.usesBundledVideo = true
                return entry
            }
            guard let count = metadata.frameCount, metadata.timing.accepts(frameCount: count) else {
                entry.message = String(localized: "Open TV Watch on your Watch to prepare the frames")
                return entry
            }
            entry.episodeCount = metadata.episodeCount
            let framePart = metadata.timing == .legacy ? "Full" : part.rawValue
            let frames = try store.widgetFrames(metadata, part: framePart, episode: metadata.episode(at: date))
            let videoPart: VideoWidgetLibrary.VideoPart
            switch part {
            case .full: videoPart = .full
            case .top: videoPart = .top
            case .bottom: videoPart = .bottom
            }
            if metadata.timing == .legacy {
                entry.video = try WidgetVideo(frames: frames, part: videoPart)
            } else {
                guard let stacked = StackedVideo(frames: frames, timing: metadata.timing, part: part) else {
                    throw ImportedVideo.Failure.invalidPackage
                }
                entry.stacked = stacked
            }
        } catch { entry.message = error.localizedDescription }
        return entry
    }
    func getSnapshot(in context: Context, completion: @escaping (PersonalVideoEntry) -> Void) {
        completion(entry())
    }
    func getTimeline(in context: Context, completion: @escaping (Timeline<PersonalVideoEntry>) -> Void) {
        let first = entry()
        guard first.episodeCount > 1 else {
            completion(Timeline(entries: [first], policy: .never))
            return
        }
        // Like AniWeather, keep one prepared episode in the extension to bound image memory.
        let next = Date(timeIntervalSince1970: (floor(first.date.timeIntervalSince1970 / 900) + 1) * 900)
        completion(Timeline(entries: [first], policy: .after(next)))
    }
}

private struct PersonalVideoEntryView: View {
    let entry: PersonalVideoEntry
    let part: VideoPart
    var body: some View {
        if entry.usesBundledVideo {
            VideoView(text: Text(entry.anchor, style: .timer), part: part)
        } else if let stacked = entry.stacked {
            StackedVideoView(video: stacked, referenceDate: entry.date)
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
    .description("Your active video: an included screensaver or your own video from iPhone. Up to 60 seconds at 2 fps.")
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
