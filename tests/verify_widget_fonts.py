"""Verify bundled widget fonts in both watchOS bundles of a release archive."""
import plistlib
import sys
from pathlib import Path


def verify(archive):
    applications = archive / "Products/Applications"
    container, = applications.glob("*.app")
    watch, = (container / "Watch").glob("*.app")
    extension, = (watch / "PlugIns").glob("*.appex")
    verify_bundles(watch, extension)


def verify_bundles(watch, extension):
    names = {"DefaultFull.ttf", "DefaultTop.ttf", "DefaultBottom.ttf"}
    for bundle in (watch, extension):
        info = plistlib.loads((bundle / "Info.plist").read_bytes())
        assert set(info.get("UIAppFonts", [])) == names, f"{bundle.name}: unexpected font declarations"
        assert {path.name for path in bundle.glob("*.ttf")} == names, f"{bundle.name}: unexpected font resources"
    resources, = extension.glob("VideoWidgetLibrary_*.bundle")
    for name in ("VideoWidgetGate.ttf", "VideoWidgetGateHalf.ttf"):
        assert (resources / name).is_file(), f"Missing package font: {name}"
        print(f"PASS: {name} supplied by the Swift package in the widget extension")
    for name in sorted(names):
        assert (watch / name).read_bytes() == (extension / name).read_bytes(), name
        print(f"PASS: {name} identical and declared in both watchOS bundles")


if __name__ == "__main__":
    verify(Path(sys.argv[1]))
