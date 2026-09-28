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

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                if let video = transfer.receivedVideo {
                    AppVideoPreview(video: video)
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

                Text("Included videos").font(.headline)
                ForEach(IncludedVideo.allCases) { included in
                    Button {
                        transfer.selectIncludedVideo(included)
                    } label: {
                        HStack {
                            Text(included.title)
                            if transfer.receivedVideo?.id == included.videoID {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                    .font(.caption2)
                }
                Text("Send a video from TV Watch on your iPhone to replace the current one.")
                    .font(.footnote)
                Text("Inspired by the 1982 Seiko TV Watch.")
                    .font(.caption2).foregroundStyle(.secondary)

            }
            .padding(.horizontal, 4)
        }
        .background(.black)
    }
}
