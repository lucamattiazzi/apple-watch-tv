import SwiftUI
import WidgetKit
import CoreGraphics

private struct PersonalVideoEntry: TimelineEntry {
    let date: Date
    var frames: [CGImage] = []
    var usesBundledVideo = false
    var message = String(localized: "Send a video from Font TV on your iPhone")
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
                entry.message = String(localized: "Open Font TV on your Watch to prepare the frames")
                return entry
            }
            entry.frames = try store.widgetFrames(metadata, part: part.rawValue)
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
        } else if entry.frames.count == 30 {
            PNGTimerMaskView(images: entry.frames, clocks: (0..<30).map {
                Text(entry.anchor.addingTimeInterval(Double($0)), style: .timer)
            }, fontName: part == .full ? "FontTVGate-Regular" : "FontTVGateHalf-Regular", rows: part.rows, alignment: part.alignment)
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
    .description("Your active video: the included Orbita animation or your own video from iPhone. 30 seconds at 1 fps.")
    .supportedFamilies([.accessoryRectangular])
    .contentMarginsDisabled()
}

struct PersonalVideoWidget: Widget {
    var body: some WidgetConfiguration {
        personalConfiguration(kind: "TVPersonalFull", title: "Font TV · Full video", part: .full)
    }
}
struct PersonalVideoTopWidget: Widget {
    var body: some WidgetConfiguration {
        personalConfiguration(kind: "TVPersonalTop", title: "Font TV · Top video", part: .top)
    }
}
struct PersonalVideoBottomWidget: Widget {
    var body: some WidgetConfiguration {
        personalConfiguration(kind: "TVPersonalBottom", title: "Font TV · Bottom video", part: .bottom)
    }
}
