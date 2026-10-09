#!/usr/bin/env python3
"""Check local BotFather media metadata; never uploads or edits the input."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    if not args.file.is_file():
        parser.error("File does not exist")
    executable = shutil.which(args.ffprobe)
    if not executable:
        parser.error("ffprobe is required; install from a trusted source")
    try:
        result = subprocess.run([executable, "-v", "error", "-show_streams",
                                 "-show_format", "-of", "json", "-i",
                                 str(args.file.resolve())], capture_output=True,
                                text=True, timeout=30, check=True)
        metadata = json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError):
        print(json.dumps({"ok": False, "error": "Unable to decode media metadata"}))
        return 1
    streams = metadata.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if len(video) != 1:
        print(json.dumps({"ok": False, "error": "Expected one image/video stream"}))
        return 1
    stream = video[0]
    dimensions = (stream.get("width"), stream.get("height"))
    codec = stream.get("codec_name")
    photo = codec in {"png", "mjpeg"}
    animation = codec in {"gif", "h264"}
    issues = []
    if photo and dimensions != (640, 360):
        issues.append("Photo must be 640x360")
    if animation and dimensions not in {(320, 180), (640, 360), (960, 540)}:
        issues.append("Animation dimensions unsupported")
    if not photo and not animation:
        issues.append("Expected PNG/JPEG, GIF, or silent H264 MP4")
    if audio:
        issues.append("Animation must have no audio")
    print(json.dumps({"ok": not issues, "codec": codec, "dimensions": dimensions,
                      "duration": metadata.get("format", {}).get("duration"),
                      "bytes": args.file.stat().st_size, "issues": issues,
                      "note": "Local metadata only; Telegram message type and acceptance unverified"}))
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
