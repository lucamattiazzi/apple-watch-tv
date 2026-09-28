import StoreKit
import SwiftUI

@MainActor
final class VideoPurchaseStore: ObservableObject {
    @Published private(set) var unlocked = false
    @Published private(set) var checking = true
    @Published private(set) var busy = false
    @Published private(set) var product: Product?
    @Published private(set) var message: String?
    private var updates: Task<Void, Never>?

    init() {
        updates = Task { [weak self] in
            for await result in Transaction.updates {
                guard let self else { return }
                guard case .verified(let transaction) = result,
                      transaction.productID == PersonalVideoAccess.productID else { continue }
                await self.refreshAccess()
                await transaction.finish()
            }
        }
    }
    deinit { updates?.cancel() }

    func refreshAccess() async {
        var purchased = false
        for await result in Transaction.currentEntitlements {
            if case .verified(let transaction) = result,
               transaction.productID == PersonalVideoAccess.productID,
               transaction.revocationDate == nil { purchased = true }
        }
        // StoreKit caches verified app transactions for offline use. Never infer
        // ownership from install date or sandbox's synthetic original version.
        var legacy = false
        do {
            if case .verified(let app) = try await AppTransaction.shared {
                legacy = PersonalVideoAccess.isLegacyPurchase(
                    originalVersion: app.originalAppVersion, isProduction: app.environment == .production)
            }
        } catch {
            if !purchased { message = String(localized: "Could not verify earlier purchases. Try Restore purchases.") }
        }
        unlocked = purchased || legacy
        if unlocked { message = nil }
        checking = false
    }
    func load() async {
        await refreshAccess()
        do {
            product = try await Product.products(for: [PersonalVideoAccess.productID]).first
            if product == nil && !unlocked {
                message = String(localized: "Purchases are currently unavailable. Included videos are always free.")
            }
        } catch { message = error.localizedDescription }
    }
    func purchase() async {
        guard !busy, !checking, !unlocked, let product else { return }
        busy = true; message = nil
        defer { busy = false }
        do {
            switch try await product.purchase() {
            case .success(let result):
                guard case .verified(let transaction) = result else {
                    message = String(localized: "The purchase could not be verified.")
                    return
                }
                await refreshAccess()
                await transaction.finish()
            case .pending:
                message = String(localized: "Purchase awaiting approval. You can keep using the included videos.")
            case .userCancelled: break
            @unknown default: break
            }
        } catch { message = error.localizedDescription }
    }
    func restore() async {
        guard !busy else { return }
        busy = true; message = nil
        defer { busy = false }
        do {
            try await AppStore.sync()
            await refreshAccess()
            if unlocked { message = String(localized: "Personal videos unlocked.") }
            else if message == nil { message = String(localized: "No previous purchase found.") }
        } catch { message = error.localizedDescription }
    }
}
