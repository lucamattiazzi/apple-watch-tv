import Foundation

@main
struct AccessPolicyTests {
    static func main() {
        precondition(PersonalVideoAccess.isLegacyPurchase(originalVersion: "21", isProduction: true))
        precondition(PersonalVideoAccess.isLegacyPurchase(originalVersion: "1", isProduction: true))
        for version in ["22", "23", "", "1.0", "invalid", "0", "-1"] {
            precondition(!PersonalVideoAccess.isLegacyPurchase(originalVersion: version, isProduction: true))
        }
        precondition(!PersonalVideoAccess.isLegacyPurchase(originalVersion: "1", isProduction: false))
        for included in [false, true] {
            for purchased in [false, true] {
                precondition(PersonalVideoAccess.canSend(isIncluded: included, unlocked: purchased) == (included || purchased))
            }
        }
        print("PASS: paid-app migration cutoff, sandbox exclusion and free/purchased access")
    }
}
