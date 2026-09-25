import SwiftUI

@main
struct TVApp: App {
    @StateObject private var transfer = VideoTransfer()
    var body: some Scene {
        WindowGroup { ContentView().environmentObject(transfer) }
    }
}

struct ContentView: View {
    @EnvironmentObject private var transfer: VideoTransfer
    @State private var anchor = Calendar.current.startOfDay(for: .now)

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                if let video = transfer.receivedVideo,
                   let store = ImportedVideoStore.shared,
                   let font = try? store.registeredFont(video, part: "Full") {
                    VideoView(text: Text(anchor, style: .timer), customFont: font)
                        .aspectRatio(16 / 9, contentMode: .fit)
                    Text(video.title).font(.headline)
                    Text("On your watch face, choose Full video, or Top video and Bottom video on Modular Duo.")
                        .font(.footnote)
                    Divider()
                }
                Text(transfer.status).font(.caption2).foregroundStyle(.secondary)
                Text(transfer.widgetPreparationStatus).font(.caption2)
                Button("Refresh widgets") {
                    transfer.refreshWidgets()
                }.font(.caption2)

                if transfer.receivedVideo?.id != ImportedVideo.bundledID {
                    Button("Restore Orbita") { transfer.restoreBundledVideo() }
                        .font(.caption2)
                } else {
                    Text("Orbita · included original animation, 30 seconds, no audio.")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                Text("Send a video from Font TV on your iPhone to replace the current one.")
                    .font(.footnote)
                Text("Inspired by the 1982 Seiko TV Watch.")
                    .font(.caption2).foregroundStyle(.secondary)

            }
            .padding(.horizontal, 4)
        }
        .background(.black)
    }
}
