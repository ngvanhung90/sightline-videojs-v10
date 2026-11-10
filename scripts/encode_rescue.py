#!/usr/bin/env python3
"""Encode locked, actual SIGHTLINE captures. SPDX-License-Identifier: Apache-2.0.

Run only through the reviewed host-storage producer. Reads manifest.json and
native 1920x1080 JPEGs from this checkout's .capture/final/. Writes only inside
a fresh D:/Codex-Project-Outputs/SIGHTLINE/rescue/recordings/<attempt>/ directory.
No resize, interpolated UI, generated soundtrack, source edits, cleanup, network,
publication, or product-acceptance claim. All intermediates and logs are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
from PIL import Image


PROJECT = Path(__file__).absolute().parent.parent
CAPTURE = PROJECT / ".capture" / "final"
RECORDINGS = Path(r"D:\Codex-Project-Outputs\SIGHTLINE\rescue\recordings")
SIZE = (1920, 1080)
FPS = 30
SAMPLE_RATE = 48000
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")
SAFE_JPEG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:jpg|jpeg)\Z", re.I)
SAFE_AUDIO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\.webm\Z", re.I)


def safe_path(raw: Path, *, must_exist: bool = False) -> Path:
    if not raw.is_absolute() or ".." in raw.parts:
        raise ValueError(f"An absolute path without traversal is required: {raw}")
    for candidate in [raw, *raw.parents]:
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if candidate.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Reparse/symlink path rejected: {candidate}")
    if must_exist and not raw.exists():
        raise ValueError(f"Missing retained input: {raw}")
    return raw.resolve()


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def epoch(value, label: str) -> float:
    result = number(value, label)
    if not 946684800 <= result <= 7258118400:
        raise ValueError(f"{label} must be an epoch timestamp in seconds")
    return result


def number(value, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def process_environment() -> dict[str, str]:
    result = os.environ.copy()
    # Read-only Git inspection and local ffmpeg must not inherit file trace/report
    # destinations outside the producer's declared recording directory.
    for key in list(result):
        if key.startswith("GIT_TRACE") or key == "FFREPORT":
            result.pop(key, None)
    result["GIT_OPTIONAL_LOCKS"] = "0"
    result["GIT_TERMINAL_PROMPT"] = "0"
    return result


def source_commit() -> str:
    safe_path(PROJECT, must_exist=True)

    def git(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=false", *arguments], cwd=PROJECT,
            env=process_environment(), capture_output=True, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        if result.returncode:
            raise RuntimeError(f"Read-only Git inspection failed: {result.stderr.strip()}")
        return result.stdout.strip()

    if Path(git("rev-parse", "--show-toplevel")).resolve() != PROJECT.resolve():
        raise ValueError("Encoder is not running from the intended checkout root")
    commit = git("rev-parse", "HEAD")
    if not COMMIT.fullmatch(commit):
        raise ValueError("Git did not return a full source commit")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Source checkout is not clean; commit and recapture before encoding")
    return commit


def capture_file(directory: Path, name, pattern: re.Pattern) -> Path:
    if not isinstance(name, str) or not pattern.fullmatch(name) or Path(name).name != name:
        raise ValueError(f"Expected a safe relative capture basename: {name!r}")
    result = safe_path(directory / name, must_exist=True)
    if result.parent != directory or not result.is_file():
        raise ValueError(f"Capture escapes the final frame directory: {name}")
    return result


def inspect_manifest(directory: Path, expected_commit: str) -> tuple[dict, list[dict], dict, bytes, str]:
    manifest_path = safe_path(directory / "manifest.json", must_exist=True)
    if not manifest_path.is_file() or manifest_path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("Missing or unexpectedly large capture manifest")
    manifest_bytes = manifest_path.read_bytes()
    if len(manifest_bytes) > 8 * 1024 * 1024:
        raise ValueError("Unexpectedly large capture manifest")
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest = json.loads(manifest_bytes.decode("utf-8-sig"))
    if not isinstance(manifest, dict) or manifest.get("source_commit") != expected_commit:
        raise ValueError("Manifest commit does not match the clean checkout HEAD")
    raw_segments = manifest.get("segments")
    if not isinstance(raw_segments, list) or not 1 <= len(raw_segments) <= 16:
        raise ValueError("Manifest must contain 1–16 actual capture segments")

    segments: list[dict] = []
    inputs: dict[str, dict] = {}
    identifiers: set[str] = set()
    frame_names: set[str] = set()
    frame_count = 0

    for raw in raw_segments:
        if not isinstance(raw, dict) or raw.get("source_commit") != expected_commit:
            raise ValueError("Every segment must declare the same full source commit")
        identifier = raw.get("id")
        if not isinstance(identifier, str) or not SAFE_ID.fullmatch(identifier) or identifier in identifiers:
            raise ValueError("Segment IDs must be unique safe basenames")
        identifiers.add(identifier)
        duration = number(raw.get("duration_seconds"), f"{identifier} duration")
        if not 0 < duration <= 90:
            raise ValueError(f"Invalid duration for {identifier}")
        frames = raw.get("frames")
        if not isinstance(frames, list) or not frames:
            raise ValueError(f"No actual frames in {identifier}")
        checked_frames = []
        previous = None
        for frame in frames:
            if not isinstance(frame, dict):
                raise ValueError(f"Invalid frame entry in {identifier}")
            image_path = capture_file(directory, frame.get("file"), SAFE_JPEG)
            if image_path.name in frame_names:
                raise ValueError("A capture file was reused; intentional holds belong in duration timing")
            frame_names.add(image_path.name)
            timestamp = epoch(frame.get("timestamp"), f"{identifier} frame timestamp")
            if previous is not None and timestamp <= previous:
                raise ValueError(f"Frame timestamps must increase strictly in {identifier}")
            previous = timestamp
            with Image.open(image_path) as image:
                if image.format != "JPEG" or image.size != SIZE or image.mode != "RGB":
                    raise ValueError(f"Native RGB JPEG 1920x1080 required; never resize {image_path.name}")
                if image.getexif().get(274, 1) != 1:
                    raise ValueError(f"Rotated EXIF capture rejected: {image_path.name}")
                image.verify()
            inputs[image_path.name] = {
                "bytes": image_path.stat().st_size, "sha256": digest(image_path), "kind": "actual-jpeg",
            }
            checked_frames.append({"path": image_path, "timestamp": timestamp})

        frame_count += len(checked_frames)
        if frame_count > 10000:
            raise ValueError("Unexpected capture count; inspect rather than encode an unbounded frame set")
        first = checked_frames[0]["timestamp"]
        last = checked_frames[-1]["timestamp"]
        span = last - first
        if duration + 0.000001 < span:
            raise ValueError(f"{identifier} duration ends before its last actual frame")
        encoded_frames = max(1, math.floor(duration * FPS + 0.5))
        segment = {
            "id": identifier, "frames": checked_frames, "duration": duration,
            "encoded_frames": encoded_frames, "encoded_duration": encoded_frames / FPS,
            "tail_hold": max(0, duration - span), "audio": None,
        }

        audio = raw.get("audio")
        if audio is not None:
            if not isinstance(audio, dict):
                raise ValueError(f"Invalid native audio declaration in {identifier}")
            audio_path = capture_file(directory, audio.get("file"), SAFE_AUDIO)
            start = epoch(audio.get("start_epoch"), f"{identifier} audio start")
            stop = epoch(audio.get("stop_epoch"), f"{identifier} audio stop")
            if not start < stop or stop - start > 180:
                raise ValueError(f"Invalid native recorder time window in {identifier}")
            overlap_start = max(first, start)
            overlap_stop = min(first + duration, stop)
            if overlap_stop <= overlap_start:
                raise ValueError(f"Declared audio has no real overlap with {identifier}; omit absent audio")
            trim = max(0, first - start)
            delay = max(0, start - first)
            segment["audio"] = {
                "path": audio_path, "start_epoch": start, "stop_epoch": stop,
                "offset": first - start, "trim": trim, "delay": delay,
                "overlap": overlap_stop - overlap_start,
                "trim_end": trim + overlap_stop - overlap_start,
            }
            inputs[audio_path.name] = {
                "bytes": audio_path.stat().st_size, "sha256": digest(audio_path), "kind": "native-recorder-webm",
            }
        segments.append(segment)

    original_total = sum(segment["duration"] for segment in segments)
    encoded_total = sum(segment["encoded_duration"] for segment in segments)
    if not 75 <= original_total <= 90 or not 75 <= encoded_total <= 90:
        raise ValueError(f"The final recording must be 75–90 seconds; declared={original_total}, CFR={encoded_total}")
    return manifest, segments, inputs, manifest_bytes, manifest_sha256


def concat_file_line(path: Path) -> str:
    value = path.as_posix()
    if any(character in value for character in ("'", "\n", "\r", "\0")):
        raise ValueError("Concat input path contains unsupported quote/control characters")
    return f"file '{value}'"


def write_exclusive(path: Path, text: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(text)


def run_ffmpeg(ffmpeg: str, arguments: list[str], log: Path) -> None:
    command = [ffmpeg, "-nostdin", "-n", "-hide_banner", "-loglevel", "info", *arguments]
    with log.open("x", encoding="utf-8") as output:
        output.write("COMMAND " + json.dumps(command) + "\n")
        output.flush()
        child = subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
            env=process_environment(),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            result = child.wait()
        except BaseException:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
            raise
        if result:
            raise RuntimeError(f"ffmpeg exited {result}; retain {log.name} and partial output")


def encode_segment(ffmpeg: str, segment: dict, output: Path, index: int) -> tuple[Path, dict]:
    stem = f"{index:02d}-{segment['id']}"
    timeline = output / f"{stem}.ffconcat"
    intermediate = output / f"{stem}.mkv"
    lines = ["ffconcat version 1.0"]
    frames = segment["frames"]
    intervals = []
    for position, frame in enumerate(frames):
        hold = (frames[position + 1]["timestamp"] - frame["timestamp"]
                if position + 1 < len(frames) else segment["tail_hold"])
        if position + 1 < len(frames):
            intervals.append(hold)
        lines.extend([concat_file_line(frame["path"]), "option framerate 1000", f"duration {hold:.6f}"])
    # The repeated final source frame makes the explicitly declared final hold
    # visible to the concat demuxer. CFR duplicates are holds, never interpolation.
    lines.extend([concat_file_line(frames[-1]["path"]), "option framerate 1000"])
    write_exclusive(timeline, "\n".join(lines) + "\n")

    duration = segment["encoded_duration"]
    arguments = ["-protocol_whitelist", "file,pipe", "-f", "concat", "-safe", "0", "-i", str(timeline)]
    audio = segment["audio"]
    if audio:
        arguments.extend(["-protocol_whitelist", "file,pipe", "-i", str(audio["path"])])
        delay_samples = round(audio["delay"] * SAMPLE_RATE)
        audio_filter = (
            "[1:a:0]asetpts=PTS-STARTPTS,"
            f"atrim=start={audio['trim']:.6f}:end={audio['trim_end']:.6f},"
            "asetpts=PTS-STARTPTS,aresample=48000,"
            "aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=stereo,"
            f"adelay=delays={delay_samples}S:all=1,apad,atrim=duration={duration:.9f},"
            "asetpts=PTS-STARTPTS[a]"
        )
    else:
        arguments.extend(["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={duration:.9f}"])
        audio_filter = f"[1:a:0]atrim=duration={duration:.9f},asetpts=PTS-STARTPTS[a]"

    # Quantize only the encoded end to a full CFR frame. Timestamp gaps remain
    # actual frame holds. No scale, crop, motion interpolation, music, or tone.
    video_filter = (
        "[0:v:0]fps=30:start_time=0:round=down,tpad=stop_mode=clone:stop_duration=0.1,"
        f"trim=duration={duration:.9f},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[v]"
    )
    arguments.extend([
        "-filter_complex", video_filter + ";" + audio_filter, "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-maxrate", "16M", "-bufsize", "32M",
        "-fps_mode", "cfr", "-r", "30",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", "-t", f"{duration:.9f}", str(intermediate),
    ])
    run_ffmpeg(ffmpeg, arguments, output / f"{stem}.encode.log")
    if not intermediate.is_file() or intermediate.stat().st_size == 0:
        raise RuntimeError(f"No encoded intermediate for {segment['id']}")

    report = {
        "id": segment["id"], "source_frame_count": len(frames),
        "first_frame_epoch": frames[0]["timestamp"], "last_frame_epoch": frames[-1]["timestamp"],
        "source_timestamp_span_seconds": frames[-1]["timestamp"] - frames[0]["timestamp"],
        "observed_mean_capture_fps": ((len(frames) - 1) / sum(intervals)) if intervals else None,
        "maximum_capture_gap_seconds": max(intervals) if intervals else None,
        "declared_tail_frame_hold_seconds": segment["tail_hold"],
        "declared_duration_seconds": segment["duration"], "encoded_duration_seconds": duration,
        "configured_cfr_frames": segment["encoded_frames"], "encoded_cfr_fps": FPS,
        "end_quantization_seconds": duration - segment["duration"],
        "audio": {
            "source": audio["path"].name if audio else None,
            "method": "native capture aligned by declared recorder epochs" if audio else "silence; no source audio declared",
            "first_frame_minus_audio_start_seconds": audio["offset"] if audio else None,
            "trimmed_audio_head_seconds": audio["trim"] if audio else 0,
            "leading_silence_seconds": audio["delay"] if audio else duration,
            "declared_captured_overlap_seconds": audio["overlap"] if audio else 0,
            "trailing_silence_seconds": max(0, duration - audio["delay"] - audio["overlap"]) if audio else 0,
            "source_recording_start_epoch": audio["start_epoch"] if audio else None,
            "source_recording_stop_epoch": audio["stop_epoch"] if audio else None,
        },
        "retained_intermediate": intermediate.name, "bytes": intermediate.stat().st_size,
    }
    return intermediate, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    directory = safe_path(args.frames, must_exist=True)
    if directory != safe_path(CAPTURE, must_exist=True) or not directory.is_dir():
        parser.error("Only this checkout's .capture/final directory is accepted")
    destination = safe_path(args.output)
    recordings = safe_path(RECORDINGS)
    if (destination.drive.upper() != "D:" or destination.name != "SIGHTLINE-review.mp4"
            or destination.parent.parent != recordings or not SAFE_ID.fullmatch(destination.parent.name)):
        parser.error("Output must be a fresh D:/Codex-Project-Outputs/SIGHTLINE/rescue/recordings/<attempt>/SIGHTLINE-review.mp4")
    if destination.exists() or (destination.parent.exists() and any(destination.parent.iterdir())):
        parser.error("Retained recording output exists; use a fresh lifecycle, never overwrite")

    commit = source_commit()
    manifest, segments, inputs, manifest_bytes, manifest_sha256 = inspect_manifest(directory, commit)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    destination.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "source_commit": commit, "source_clean_before": True,
        "encoder_sha256": digest(Path(__file__)), "manifest_sha256": manifest_sha256,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_native_dimensions": list(SIZE), "output_dimensions": list(SIZE),
        "output_fps": FPS, "native_30fps_capture_claim": False,
        "cadence": "Actual screenshot timestamps are held; output alone is H.264 CFR 30. No interpolation or resizing.",
        "audio": "Only declared native MediaRecorder audio; absent intervals are silence. Final AAC stereo 48kHz 160kbps.",
        "source_epoch_alignment_limit": "Alignment follows declared recorder epochs and first decoded sample; perceptual sync still requires real playback QA.",
        "inputs": inputs, "segments": [], "product_acceptance": False, "visual_audio_sync_acceptance": False,
    }
    with (destination.parent / "manifest.snapshot.json").open("xb") as snapshot:
        snapshot.write(manifest_bytes)
    try:
        intermediates = []
        for index, segment in enumerate(segments, 1):
            intermediate, detail = encode_segment(ffmpeg, segment, destination.parent, index)
            intermediates.append((intermediate, segment["encoded_duration"]))
            report["segments"].append(detail)
            print(json.dumps({"segment": segment["id"], "encoded": True, "acceptance": False}), flush=True)
        total = sum(duration for _, duration in intermediates)
        final_concat = destination.parent / "final.ffconcat"
        lines = ["ffconcat version 1.0"]
        for intermediate, duration in intermediates:
            lines.extend([concat_file_line(intermediate), f"duration {duration:.9f}"])
        write_exclusive(final_concat, "\n".join(lines) + "\n")
        run_ffmpeg(ffmpeg, [
            "-protocol_whitelist", "file,pipe", "-f", "concat", "-safe", "0", "-i", str(final_concat),
            "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
            "-ar", "48000", "-ac", "2", "-t", f"{total:.9f}", "-movflags", "+faststart", str(destination),
        ], destination.parent / "final.encode.log")
        if not destination.is_file() or not destination.stat().st_size:
            raise RuntimeError("No final MP4 produced")
        probe_log = destination.parent / "final.streamcopy-check.log"
        run_ffmpeg(ffmpeg, [
            "-protocol_whitelist", "file,pipe", "-i", str(destination), "-map", "0:v:0", "-map", "0:a:0",
            "-c", "copy", "-progress", "pipe:1", "-nostats", "-f", "null", "-",
        ], probe_log)
        probe_text = probe_log.read_text(encoding="utf-8", errors="replace")
        counted_frames = re.findall(r"^frame=\s*(\d+)\s*$", probe_text, re.M)
        counted_time = re.findall(r"^out_time_us=\s*(\d+)\s*$", probe_text, re.M)
        expected_frames = sum(segment["encoded_frames"] for segment in segments)
        if not counted_frames or int(counted_frames[-1]) != expected_frames:
            raise RuntimeError("Final stream-copy frame count does not match the configured CFR timeline")
        report["final_streamcopy_frame_count"] = int(counted_frames[-1])
        if not counted_time:
            raise RuntimeError("Final stream-copy progress time is missing")
        progress_seconds = int(counted_time[-1]) / 1_000_000
        report["final_streamcopy_progress_seconds"] = progress_seconds
        report["final_progress_duration_error_seconds"] = progress_seconds - total
        report["final_progress_duration_tolerance_seconds"] = 0.1
        if abs(progress_seconds - total) > 0.1 + 1e-9:
            raise RuntimeError("Final stream-copy progress differs from the configured timeline by more than 0.1 seconds")
        report["streamcopy_check_limit"] = "Container packet/frame counting, not a full perceptual or decoded-frame audit."
        if source_commit() != commit:
            raise ValueError("Source commit changed while encoding")
        for name, original in inputs.items():
            if digest(safe_path(directory / name, must_exist=True)) != original["sha256"]:
                raise ValueError(f"Retained capture changed while encoding: {name}")
        if digest(safe_path(directory / "manifest.json", must_exist=True)) != manifest_sha256:
            raise ValueError("Capture manifest changed while encoding")
        report.update({
            "encoding_status": "ENCODED_NOT_VISUALLY_ACCEPTED", "source_clean_after": True,
            "encoded_duration_seconds": total, "output": str(destination),
            "output_bytes": destination.stat().st_size, "output_sha256": digest(destination),
        })
    except BaseException as error:
        report.update({"encoding_status": "FAILED_OUTPUTS_RETAINED", "error": f"{type(error).__name__}: {error}"})
        write_exclusive(destination.parent / "encode-report.json", json.dumps(report, indent=2) + "\n")
        raise
    write_exclusive(destination.parent / "encode-report.json", json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(destination), "report": str(destination.parent / "encode-report.json"),
                      "duration_seconds": total, "product_acceptance": False}), flush=True)


if __name__ == "__main__":
    main()
