import SwiftUI
import CoreText
import PhotosUI
import UniformTypeIdentifiers
import CoreTransferable

struct PickedMovie: Transferable {
    let url: URL
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(importedContentType: .movie) { received in
            let url = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
                .appendingPathExtension(received.file.pathExtension)
            try FileManager.default.copyItem(at: received.file, to: url)
            return PickedMovie(url: url)
        }
    }
}

@MainActor
final class PhoneVideoModel: ObservableObject {
    @Published var video: ImportedVideo?
    @Published var busy = false
    @Published var error: String?
    @Published var previewFont: CTFont?
    let store = ImportedVideoStore(root: FileManager.default.urls(for: .applicationSupportDirectory,
        in: .userDomainMask)[0].appendingPathComponent("PhoneVideos"))

    init() {
        do {
            video = try store.loadInitialVideo()
            if let video { previewFont = try store.registeredFont(video, part: "Full") }
        } catch { self.error = error.localizedDescription }
    }
    func convert(_ url: URL, title: String) async {
        busy = true; error = nil
        defer { busy = false; try? FileManager.default.removeItem(at: url) }
        do {
            let imported = try await Task.detached(priority: .userInitiated) {
                try await VideoConverter.convert(url: url, title: title)
            }.value
            try store.install(imported)
            previewFont = try store.registeredFont(imported, part: "Full")
            video = imported
        } catch { self.error = error.localizedDescription }
    }
}

@main
struct PhoneApp: App {
    @StateObject private var transfer = VideoTransfer()
    var body: some Scene { WindowGroup { PhoneContentView().environmentObject(transfer) } }
}

struct PhoneContentView: View {
    @EnvironmentObject private var transfer: VideoTransfer
    @StateObject private var model = PhoneVideoModel()
    @State private var selection: PhotosPickerItem?
    @State private var showFiles = false
    @State private var anchor = Calendar.current.startOfDay(for: .now)

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    Text("A video on your watch face")
                        .font(.largeTitle.bold())
                    Text("Choose a video. The first 30 seconds become a black-and-white loop at 1 fps. Shorter videos repeat; the aspect ratio is preserved.")
                        .foregroundStyle(.secondary)
                    Text("One video at a time: each new transfer replaces the video on your Watch.")
                        .font(.callout)
                    HStack {
                        PhotosPicker(selection: $selection, matching: .videos) {
                            Label("From Photos", systemImage: "photo.on.rectangle")
                        }
                        Button { showFiles = true } label: { Label("From Files", systemImage: "folder") }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(model.busy)
                    if model.busy { ProgressView("Preparing video…") }
                    if let error = model.error { Text(error).foregroundStyle(.red) }
                    if let video = model.video, let font = model.previewFont {
                        VideoView(text: Text(anchor, style: .timer), customFont: font)
                            .aspectRatio(16 / 9, contentMode: .fit)
                        Text(video.title).font(.headline)
                        Button {
                            do { try transfer.send(video) } catch { model.error = error.localizedDescription }
                        } label: { Label("Send to Watch", systemImage: "applewatch.radiowaves.left.and.right") }
                        .buttonStyle(.borderedProminent)
                        .disabled(model.busy)
                    }
                    Text(transfer.status).font(.callout).foregroundStyle(.secondary)
                    Divider()
                    Text("On your Watch").font(.headline)
                    Text("Orbita, an original animation, is already included on your Watch. You can replace it with your own video and restore it from your Watch.")
                    Text("For your watch face, choose Full video, or Top video and Bottom video on Modular Duo.")
                    Text("Your video is processed on your iPhone and transferred to your paired Watch. It is not uploaded to a server.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Text("Inspired by the 1982 Seiko TV Watch.")
                        .font(.footnote).foregroundStyle(.secondary)
                    Link("The history of the Seiko TV Watch", destination: URL(string: "https://museum.seiko.co.jp/en/collections/watch_latestage/collect040/")!)
                        .font(.footnote)
                }
                .padding(24)
            }
            .navigationTitle("Font TV")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onChange(of: selection) { _, item in
            guard let item else { return }
            model.busy = true
            Task {
                do {
                    guard let movie = try await item.loadTransferable(type: PickedMovie.self) else {
                        throw VideoConverter.Failure.noVideo
                    }
                    await model.convert(movie.url, title: String(localized: "Video from Photos"))
                } catch { model.error = error.localizedDescription; model.busy = false }
                selection = nil
            }
        }
        .fileImporter(isPresented: $showFiles, allowedContentTypes: [.movie, .video]) { result in
            do {
                let url = try result.get()
                let access = url.startAccessingSecurityScopedResource()
                defer { if access { url.stopAccessingSecurityScopedResource() } }
                let copy = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
                    .appendingPathExtension(url.pathExtension)
                try FileManager.default.copyItem(at: url, to: copy)
                model.busy = true
                Task { await model.convert(copy, title: url.deletingPathExtension().lastPathComponent) }
            } catch { model.error = error.localizedDescription }
        }
    }
}
