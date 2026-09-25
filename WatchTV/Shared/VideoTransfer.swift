import Foundation
import Combine
import WatchConnectivity
#if os(watchOS)
import WidgetKit
#endif

@MainActor
final class VideoTransfer: NSObject, ObservableObject, WCSessionDelegate {
    @Published private(set) var status = String(localized: "Connecting to Watch…")
    @Published private(set) var receivedVideo: ImportedVideo?
    @Published private(set) var ready = false
    @Published private(set) var widgetPreparationStatus = ""
    private var preparingWidgets = false
    private var pendingTransferID: String? = UserDefaults.standard.string(forKey: "pendingTransferID")
    private var pendingID: String? = UserDefaults.standard.string(forKey: "pendingVideoID")
    private var receivedID: String? = UserDefaults.standard.string(forKey: "receivedVideoID")

    override init() {
        super.init()
        #if os(watchOS)
        do {
            guard let store = ImportedVideoStore.shared else { throw ImportedVideo.Failure.unavailableStorage }
            receivedVideo = try store.loadInitialVideo()
        } catch { status = error.localizedDescription }
        refreshWidgets()
        #endif
        if WCSession.isSupported() {
            WCSession.default.delegate = self
            WCSession.default.activate()
        } else { status = String(localized: "Transfer is available on paired devices.") }
    }

    #if os(watchOS)
    func restoreBundledVideo() {
        do {
            guard let store = ImportedVideoStore.shared else { throw ImportedVideo.Failure.unavailableStorage }
            let video = try ImportedVideo.bundled()
            try store.install(video)
            receivedVideo = video
            status = String(localized: "Included video restored.")
            refreshWidgets()
        } catch { status = error.localizedDescription }
    }
    func refreshWidgets() {
        guard !preparingWidgets else { return }
        guard let video = receivedVideo, let store = ImportedVideoStore.shared else {
            widgetPreparationStatus = String(localized: "No video available.")
            WidgetCenter.shared.reloadAllTimelines()
            return
        }
        preparingWidgets = true
        widgetPreparationStatus = String(localized: "Preparing 30 frames…")
        Task {
            let result = await Task.detached(priority: .userInitiated) {
                Result { try store.prepareWidgetAssets(video) }
            }.value
            preparingWidgets = false
            // An import may arrive while the previous video is being rasterized.
            guard receivedVideo?.id == video.id else { refreshWidgets(); return }
            switch result {
            case .success:
                widgetPreparationStatus = String(localized: "30 frames ready for widgets.")
                WidgetCenter.shared.reloadAllTimelines()
            case .failure(let error):
                widgetPreparationStatus = String(localized: "Widget preparation: \(error.localizedDescription)")
            }
        }
    }
    #endif

    #if os(iOS)
    func send(_ video: ImportedVideo) throws {
        let session = WCSession.default
        guard session.activationState == .activated, session.isPaired, session.isWatchAppInstalled else {
            status = String(localized: "Open Font TV on your paired Watch, then try again.")
            return
        }
        let directory = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("OutgoingVideos")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let transferID = UUID().uuidString
        let url = directory.appendingPathComponent(transferID + ".video")
        try video.encoded().write(to: url, options: .atomic)
        pendingTransferID = transferID
        UserDefaults.standard.set(transferID, forKey: "pendingTransferID")
        pendingID = video.id.uuidString
        UserDefaults.standard.set(pendingID, forKey: "pendingVideoID")
        for transfer in session.outstandingFileTransfers { transfer.cancel() }
        session.transferFile(url, metadata: ["videoID": video.id.uuidString, "transferID": transferID])
        status = String(localized: "Queued for your Watch. The transfer can continue in the background.")
    }

    nonisolated func sessionDidBecomeInactive(_ session: WCSession) {
        Task { @MainActor in self.ready = false }
    }
    nonisolated func sessionDidDeactivate(_ session: WCSession) { session.activate() }
    nonisolated func sessionWatchStateDidChange(_ session: WCSession) {
        Task { @MainActor in self.ready = session.isPaired && session.isWatchAppInstalled }
    }
    #endif

    nonisolated func session(_ session: WCSession, activationDidCompleteWith state: WCSessionActivationState,
                             error: Error?) {
        Task { @MainActor in
            self.ready = state == .activated
            if let error { self.status = error.localizedDescription; return }
            #if os(iOS)
            self.ready = self.ready && session.isPaired && session.isWatchAppInstalled
            self.status = self.pendingID == nil ? String(localized: "Choose a video to send to your Watch.") : String(localized: "Waiting for confirmation from your Watch.")
            self.acceptAcknowledgement(session.receivedApplicationContext)
            #else
            self.status = self.receivedVideo == nil ? String(localized: "Choose a video in the iPhone app.") : String(localized: "Video ready.")
            if let video = self.receivedVideo {
                try? session.updateApplicationContext(["receivedID": video.id.uuidString, "receivedTitle": video.title])
            }
            #endif
        }
    }

    nonisolated func session(_ session: WCSession, didReceive file: WCSessionFile) {
        #if os(watchOS)
        // WCSession deletes its temporary file when this callback returns.
        // Complete the local copy and atomic publication before returning.
        do {
            let size = try file.fileURL.resourceValues(forKeys: [.fileSizeKey]).fileSize ?? 0
            guard size <= 24_000_000 else { throw ImportedVideo.Failure.invalidPackage }
            let video = try PropertyListDecoder().decode(ImportedVideo.self, from: Data(contentsOf: file.fileURL))
            guard let store = ImportedVideoStore.shared else { throw ImportedVideo.Failure.unavailableStorage }
            try store.install(video)
            try? session.updateApplicationContext(["receivedID": video.id.uuidString, "receivedTitle": video.title])
            Task { @MainActor in
                guard store.current()?.id == video.id else { return }
                self.receivedVideo = video
                self.refreshWidgets()
                self.status = String(localized: "Custom video received.")
            }
        } catch {
            let id = file.metadata?["videoID"] as? String ?? ""
            try? session.updateApplicationContext(["failedID": id, "failure": error.localizedDescription])
            Task { @MainActor in self.status = error.localizedDescription }
        }
        #endif
    }

    nonisolated func session(_ session: WCSession, didReceiveApplicationContext context: [String: Any]) {
        Task { @MainActor in self.acceptAcknowledgement(context) }
    }
    private func acceptAcknowledgement(_ context: [String: Any]) {
        if let id = context["receivedID"] as? String, id == pendingID {
            receivedID = id
            UserDefaults.standard.set(id, forKey: "receivedVideoID")
            status = String(localized: "Received on your Watch. Open Font TV on your Watch to see it.")
        } else if let id = context["failedID"] as? String, id == pendingID {
            status = context["failure"] as? String ?? String(localized: "Your Watch could not import the video.")
        }
    }
    nonisolated func session(_ session: WCSession, didFinish transfer: WCSessionFileTransfer, error: Error?) {
        let id = transfer.file.metadata?["videoID"] as? String
        let transferID = transfer.file.metadata?["transferID"] as? String
        try? FileManager.default.removeItem(at: transfer.file.fileURL)
        Task { @MainActor in
            guard transferID == self.pendingTransferID, id == self.pendingID, id != self.receivedID else { return }
            if let error { self.status = String(localized: "Transfer failed: \(error.localizedDescription)") }
            else { self.status = String(localized: "Transferred. Waiting for your Watch to confirm the import.") }
        }
    }
}
