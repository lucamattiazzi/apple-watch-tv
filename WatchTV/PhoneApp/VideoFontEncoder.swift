import Foundation

/// Replaces the outlines in our bundled timer font, preserving its tested GSUB codec.
/// The generated asset contains images and font tables, never executable code.
enum VideoFontEncoder {
    enum Failure: Error { case invalidFrames, invalidTemplate }

    static func encode(frames: [[UInt8]], part: String, template: Data, family: String) throws -> Data {
        guard frames.count == 30, frames.allSatisfy({ $0.count == 96 * 54 && $0.allSatisfy { $0 < 6 } }),
              ["Full", "Top", "Bottom"].contains(part) else { throw Failure.invalidFrames }
        let source = [UInt8](template)
        guard source.count >= 12 else { throw Failure.invalidTemplate }
        let count = read16(source, 4)
        guard source.count >= 12 + count * 16 else { throw Failure.invalidTemplate }
        var tables: [String: [UInt8]] = [:]
        for i in 0..<count {
            let record = 12 + i * 16
            let tag = String(bytes: source[record..<record + 4], encoding: .ascii)!
            let offset = Int(read32(source, record + 8)), size = Int(read32(source, record + 12))
            guard offset <= source.count, size <= source.count - offset else { throw Failure.invalidTemplate }
            tables[tag] = Array(source[offset..<offset + size])
        }
        guard let head = tables["head"], head.count >= 54,
              let hhea = tables["hhea"], hhea.count >= 36,
              let maxp = tables["maxp"], maxp.count >= 32,
              read16(maxp, 4) == 43, tables["GSUB"] != nil else { throw Failure.invalidTemplate }
        let first = part == "Bottom" ? 27 : 0
        let last = part == "Top" ? 27 : 54
        var glyphs: [[UInt8]] = [[], [], []]
        var bounds: [(Int, Int, Int, Int)] = [(0,0,0,0), (0,0,0,0), (0,0,0,0)]
        var maxPoints = 0, maxContours = 0
        var pictures: [[UInt8]] = []
        var pictureBounds: [(Int, Int, Int, Int)] = []
        for frame in frames {
            var points: [(Int, Int)] = []
            for y in first..<last {
                for x in 0..<96 {
                    // Matches the six area-coverage levels of the bundled Python encoder.
                    let side = Int((32 * sqrt(Double(frame[y * 96 + x]) / 5)).rounded())
                    if side == 0 { continue }
                    let left = x * 32 + (32 - side) / 2
                    let bottom = (last - y - 1) * 32 + (32 - side) / 2
                    points += [(left,bottom), (left,bottom + side), (left + side,bottom + side), (left + side,bottom)]
                }
            }
            let box = (points.map { $0.0 }.min() ?? 0, points.map { $0.1 }.min() ?? 0,
                       points.map { $0.0 }.max() ?? 0, points.map { $0.1 }.max() ?? 0)
            var glyph: [UInt8] = []
            put16(&glyph, points.count / 4)
            for value in [box.0, box.1, box.2, box.3] { put16(&glyph, value) }
            for contour in 0..<(points.count / 4) { put16(&glyph, contour * 4 + 3) }
            put16(&glyph, 0) // No instructions.
            glyph += [UInt8](repeating: 1, count: points.count) // On-curve, signed 16-bit deltas.
            var previous = 0
            for point in points { put16(&glyph, point.0 - previous); previous = point.0 }
            previous = 0
            for point in points { put16(&glyph, point.1 - previous); previous = point.1 }
            pictures.append(glyph)
            pictureBounds.append(box)
            maxPoints = max(maxPoints, points.count)
            maxContours = max(maxContours, points.count / 4)
        }
        glyphs += Array(pictures.prefix(10)) + pictures
        bounds += Array(pictureBounds.prefix(10)) + pictureBounds
        var glyf: [UInt8] = [], loca: [UInt8] = [], hmtx: [UInt8] = []
        for i in glyphs.indices {
            put32(&loca, UInt32(glyf.count))
            glyf += glyphs[i]
            while glyf.count % 4 != 0 { glyf.append(0) }
            put16(&hmtx, i == 1 || i == 2 ? 0 : 3072)
            put16(&hmtx, bounds[i].0)
        }
        put32(&loca, UInt32(glyf.count))
        tables["glyf"] = glyf; tables["loca"] = loca; tables["hmtx"] = hmtx
        set32(&tables["head"]!, 8, 0)
        for (offset, value) in [(36,0), (38,0), (40,3072), (42,(last-first)*32), (50,1)] {
            set16(&tables["head"]!, offset, value)
        }
        for (offset, value) in [(10,3072), (12,0), (14,0), (16,3072), (34,43)] {
            set16(&tables["hhea"]!, offset, value)
        }
        set16(&tables["maxp"]!, 6, maxPoints)
        set16(&tables["maxp"]!, 8, maxContours)
        tables["name"] = nameTable(family)
        let tags = tables.keys.sorted()
        let power = Int(log2(Double(tags.count)))
        var result: [UInt8] = []
        put32(&result, 0x00010000)
        for value in [tags.count, (1 << power)*16, power, tags.count*16 - (1 << power)*16] {
            put16(&result, value)
        }
        var payload: [UInt8] = [], headOffset = 0
        for tag in tags {
            let bytes = tables[tag]!
            let offset = 12 + tags.count * 16 + payload.count
            if tag == "head" { headOffset = offset }
            result += Array(tag.utf8)
            put32(&result, checksum(bytes)); put32(&result, UInt32(offset)); put32(&result, UInt32(bytes.count))
            payload += bytes
            while payload.count % 4 != 0 { payload.append(0) }
        }
        result += payload
        set32(&result, headOffset + 8, 0xB1B0AFBA &- checksum(result))
        return Data(result)
    }

    private static func nameTable(_ family: String) -> [UInt8] {
        let names = [(1,family), (2,"Regular"), (3,family + "-Regular"),
                     (4,family + " Regular"), (5,"Version 1.000"), (6,family + "-Regular")]
        var result: [UInt8] = [], strings: [UInt8] = []
        put16(&result, 0); put16(&result, names.count); put16(&result, 6 + names.count * 12)
        for (id, value) in names {
            let bytes = Array(value.data(using: .utf16BigEndian)!)
            for n in [3,1,0x409,id,bytes.count,strings.count] { put16(&result,n) }
            strings += bytes
        }
        return result + strings
    }
    private static func read16(_ b: [UInt8], _ i: Int) -> Int { Int(b[i]) << 8 | Int(b[i+1]) }
    private static func read32(_ b: [UInt8], _ i: Int) -> UInt32 {
        UInt32(read16(b,i)) << 16 | UInt32(read16(b,i+2))
    }
    private static func put16(_ b: inout [UInt8], _ n: Int) {
        let v = UInt16(truncatingIfNeeded: n); b += [UInt8(v >> 8), UInt8(v & 255)]
    }
    private static func put32(_ b: inout [UInt8], _ n: UInt32) {
        b += [UInt8(n >> 24), UInt8((n >> 16) & 255), UInt8((n >> 8) & 255), UInt8(n & 255)]
    }
    private static func set16(_ b: inout [UInt8], _ i: Int, _ n: Int) {
        var bytes: [UInt8] = []; put16(&bytes,n); b.replaceSubrange(i..<i+2,with:bytes)
    }
    private static func set32(_ b: inout [UInt8], _ i: Int, _ n: UInt32) {
        var bytes: [UInt8] = []; put32(&bytes,n); b.replaceSubrange(i..<i+4,with:bytes)
    }
    private static func checksum(_ b: [UInt8]) -> UInt32 {
        var padded = b
        while padded.count % 4 != 0 { padded.append(0) }
        return stride(from:0,to:padded.count,by:4).reduce(UInt32(0)) { $0 &+ read32(padded,$1) }
    }
}
