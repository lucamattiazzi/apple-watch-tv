import SwiftUI
import WidgetKit

@main
struct TVWidgetBundle: WidgetBundle {
    var body: some Widget {
        PersonalVideoWidget()
        PersonalVideoTopWidget()
        PersonalVideoBottomWidget()
    }
}
