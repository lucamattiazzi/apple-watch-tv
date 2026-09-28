import XCTest
import StoreKitTest
@testable import FontTV

@MainActor
final class PurchaseTests: XCTestCase {
    func testPurchaseRestoreAndRefund() async throws {
        let url = try XCTUnwrap(Bundle(for: Self.self).url(forResource: "TVWatch", withExtension: "storekit"))
        let session = try SKTestSession(contentsOf: url)
        session.resetToDefaultState()
        session.clearTransactions()
        session.disableDialogs = true
        defer { session.clearTransactions() }
        let store = VideoPurchaseStore()
        await store.load()
        XCTAssertFalse(store.unlocked, "Fresh install must remain free")
        _ = try XCTUnwrap(store.product)
        await store.purchase()
        XCTAssertTrue(store.unlocked, "Verified purchase must unlock personal videos")
        let restored = VideoPurchaseStore()
        await restored.load()
        XCTAssertTrue(restored.unlocked, "Recreated store must recover entitlement")
        await restored.restore()
        XCTAssertTrue(restored.unlocked)
        let transaction = try XCTUnwrap(session.allTransactions().first)
        try session.refundTransaction(identifier: transaction.identifier)
        await store.refreshAccess()
        XCTAssertFalse(store.unlocked, "Refund must remove entitlement")
    }
}
