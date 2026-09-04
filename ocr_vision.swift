import Vision
import AppKit

// Usage: swift ocr_vision.swift <image-path> [language1 language2 ...]
// Defaults: zh-Hans, en-US. Prints recognized text lines with normalized
// layout coords (top-left origin y, left x), sorted top-to-bottom, left-to-right.

let args = CommandLine.arguments
guard args.count > 1 else {
    print("Usage: swift ocr_vision.swift <image-path> [language1 language2 ...]")
    exit(1)
}
let path = args[1]
let langs = args.count > 2 ? Array(args.dropFirst(2)) : ["zh-Hans", "en-US"]

guard let img = NSImage(contentsOfFile: path) else {
    print("ERR: cannot load image at \(path)")
    exit(1)
}
var rect = NSRect(origin: .zero, size: img.size)
guard let cg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
    print("ERR: cannot make cgImage")
    exit(1)
}

let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = langs
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
try handler.perform([req])

let results = (req.results ?? []).sorted {
    let y0 = 1 - $0.boundingBox.origin.y - $0.boundingBox.height
    let y1 = 1 - $1.boundingBox.origin.y - $1.boundingBox.height
    if abs(y0 - y1) > 0.01 { return y0 < y1 }
    return $0.boundingBox.origin.x < $1.boundingBox.origin.x
}
for obs in results {
    if let t = obs.topCandidates(1).first {
        let b = obs.boundingBox
        print(String(format: "y=%.3f x=%.3f | %@", 1 - b.origin.y - b.height, b.origin.x, t.string))
    }
}
