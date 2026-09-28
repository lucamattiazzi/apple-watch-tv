import Foundation

/// Build 22 is the first free build. On iOS originalAppVersion is CFBundleVersion.
enum PersonalVideoAccess {
    static let productID = "com.tvwatch.fonthack.personalvideos"
    static func isLegacyPurchase(originalVersion: String, isProduction: Bool) -> Bool {
        guard isProduction, let build = Int(originalVersion) else { return false }
        return build > 0 && build < 22
    }
    static func canSend(isIncluded: Bool, unlocked: Bool) -> Bool { isIncluded || unlocked }
}
