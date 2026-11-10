#!/usr/bin/env python3
"""Original SIGHTLINE eight-tap instructional media. SPDX-License-Identifier: Apache-2.0.

Run ONLY through the Owner's reviewed host-storage producer. This script has no
network access, downloads, browser automation, player drawing, or frame tree.
Frames stream into ffmpeg. Generated instructional media/audio/VTT are CC0-1.0.

Example (not authorization to execute):
  python -B generate_lesson.py --output D:\\...\\lesson-v1 --width 1920 --fps 30

The original presentation teaches an eight-tap hand sequence. It makes no claim
that the sequence itself was invented or that a named musical technique is taught.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import subprocess
import sys
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


DURATION = 40
SAMPLE_RATE = 48_000
PATTERN = tuple("LRLLRLRR")
EVENT_OFFSET = 0.25
INTERVAL = 0.5
PHASES = (
    (0.0, "Listen first", "Listen once. Then use your hands."),
    (8.0, "Left / right", "L is your left hand. R is your right."),
    (16.0, "Catch the doubles", "Keep the gaps equal, even on a double."),
    (24.0, "Try together", "Follow all eight taps. Then repeat."),
    (32.0, "Your turn", "One guided round. Then no hand hints."),
)
PALETTE = {
    "desk": "#252822",
    "panel": "#2d312a",
    "ink": "#f4f1e7",
    "muted": "#b9c0b1",
    "faint": "#737d6b",
    "line": "#69745f",
    "accent": "#deefa8",
    "accent_ink": "#242d20",
}


@dataclass(frozen=True)
class TapEvent:
    time: float
    section: int
    beat: int
    kind: str
    hand: str | None


def make_events() -> list[TapEvent]:
    events: list[TapEvent] = []
    for beat in range(4):
        events.append(TapEvent(EVENT_OFFSET + beat * INTERVAL, 0, beat, "count-in", None))
    for beat, hand in enumerate(PATTERN):
        events.append(TapEvent(2.0 + EVENT_OFFSET + beat * INTERVAL, 0, beat, "tap", hand))
    for section in range(1, 5):
        for cycle in range(2):
            for beat, hand in enumerate(PATTERN):
                memory = section == 4 and cycle == 1
                events.append(TapEvent(section * 8.0 + cycle * 4.0 + EVENT_OFFSET + beat * INTERVAL,
                                       section, beat, "memory-tick" if memory else "tap",
                                       None if memory else hand))
    return sorted(events, key=lambda event: event.time)


EVENTS = make_events()
EVENT_TIMES = [event.time for event in EVENTS]


def source_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    # Installed fonts are rasterized into footage; font files are never copied.
    windows = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf"] if bold else [
        "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]
    linux = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for candidate in [*windows, *linux]:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    raise RuntimeError("No reviewed installed sans-serif font found; do not download a replacement automatically.")


def mix_hex(a: str, b: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    aa = tuple(int(a[index:index + 2], 16) for index in (1, 3, 5))
    bb = tuple(int(b[index:index + 2], 16) for index in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(aa, bb))


class LessonScene:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.portrait = height > width
        self.scale = width / (432 if self.portrait else 1920)
        self.fonts: dict[tuple[int, bool], ImageFont.ImageFont] = {}
        self.background = Image.new("RGB", (width, height), PALETTE["desk"])

    def font(self, size: float, bold: bool = False) -> ImageFont.ImageFont:
        key = (max(10, round(size * self.scale)), bold)
        if key not in self.fonts:
            self.fonts[key] = source_font(*key)
        return self.fonts[key]

    def text(self, draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str,
             size: float, color: str = "ink", bold: bool = False, anchor: str = "mm") -> None:
        draw.text((round(xy[0]), round(xy[1])), value, fill=PALETTE.get(color, color),
                  font=self.font(size, bold), anchor=anchor)

    def wrapped(self, draw: ImageDraw.ImageDraw, center_x: float, y: float, value: str,
                size: float, max_width: float, color: str = "muted", line_height: float = 1.3) -> None:
        lines: list[str] = []
        line = ""
        font = self.font(size)
        for word in value.split():
            candidate = f"{line} {word}".strip()
            if line and draw.textlength(candidate, font=font) > max_width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
        for index, text in enumerate(lines):
            self.text(draw, (center_x, y + index * size * self.scale * line_height), text,
                      size=size, color=color)

    def frame(self, time: float) -> Image.Image:
        image = self.background.copy()
        draw = ImageDraw.Draw(image)
        section = min(4, max(0, int(time // 8)))
        event_index = bisect.bisect_right(EVENT_TIMES, time) - 1
        event = EVENTS[event_index] if event_index >= 0 else None
        age = time - event.time if event is not None else float("inf")
        in_section = event is not None and event.section == section
        pulse = max(0.0, 1.0 - age / 0.28) if in_section and age >= 0 else 0.0
        active_hand = event.hand if in_section and event.kind == "tap" and age < 0.25 else None
        current_beat = event.beat if in_section and age < 0.5 and event.kind != "count-in" else None
        memory = time >= 36.0
        count_in = time < 2.0
        quiet_listen = 6.0 <= time < 8.0
        phase_title = PHASES[section][1]
        instruction = PHASES[section][2]
        if memory:
            instruction = "No hand hints. Keep the same eight taps."
        elif quiet_listen:
            instruction = "That was one pattern. Try it next."

        if self.portrait:
            self.draw_portrait(draw, time, section, phase_title, instruction, event,
                               in_section, pulse, active_hand, current_beat, memory, count_in)
        else:
            self.draw_landscape(draw, time, section, phase_title, instruction, event,
                                in_section, pulse, active_hand, current_beat, memory, count_in)
        return image

    def hand_diagram(self, draw: ImageDraw.ImageDraw, center_x: float, center_y: float,
                     radius: float, hand: str, active: bool, pulse: float) -> None:
        radius = round(radius)
        ring_extra = round((5 + pulse * 10) * self.scale)
        if active:
            draw.ellipse((center_x - radius - ring_extra, center_y - radius - ring_extra,
                          center_x + radius + ring_extra, center_y + radius + ring_extra),
                         outline=mix_hex(PALETTE["line"], PALETTE["accent"], pulse),
                         width=max(2, round(2 * self.scale)))
        fill = PALETTE["accent"] if active else PALETTE["panel"]
        outline = PALETTE["accent"] if active else PALETTE["line"]
        draw.ellipse((center_x - radius, center_y - radius, center_x + radius, center_y + radius),
                     fill=fill, outline=outline, width=max(2, round(2 * self.scale)))
        letter_size = 62 if self.portrait else 132
        self.text(draw, (center_x, center_y - 3 * self.scale), hand, letter_size,
                  "accent_ink" if active else "ink", bold=True)
        label_y = center_y + radius + (27 if self.portrait else 48) * self.scale
        self.text(draw, (center_x, label_y), "LEFT HAND" if hand == "L" else "RIGHT HAND",
                  12 if self.portrait else 26, color="muted", bold=True)

    def pattern_row(self, draw: ImageDraw.ImageDraw, center_y: float, current_beat: int | None,
                    section: int, time: float, memory: bool, count_in: bool) -> None:
        if self.portrait:
            self.portrait_pattern(draw, center_y, current_beat, section, time, memory, count_in)
            return
        unit = (45 if self.portrait else 112) * self.scale
        centers = [self.width / 2 + (index - 3.5) * unit for index in range(8)]
        box_w = (36 if self.portrait else 82) * self.scale
        box_h = (47 if self.portrait else 92) * self.scale
        for index, (x, hand) in enumerate(zip(centers, PATTERN)):
            active = current_beat == index and not count_in
            rectangle = (round(x - box_w / 2), round(center_y - box_h / 2),
                         round(x + box_w / 2), round(center_y + box_h / 2))
            if active:
                draw.rounded_rectangle(rectangle, radius=round(5 * self.scale),
                                       fill=PALETTE["accent"], outline=PALETTE["accent"])
            else:
                draw.rounded_rectangle(rectangle, radius=round(5 * self.scale),
                                       outline=PALETTE["line"], width=max(1, round(self.scale)))
            value = "·" if memory else hand
            self.text(draw, (x, center_y - 2 * self.scale), value,
                      26 if self.portrait else 54,
                      "accent_ink" if active else ("faint" if count_in else "ink"), bold=True)
            self.text(draw, (x, center_y + (37 if self.portrait else 73) * self.scale),
                      str(index + 1), 11 if self.portrait else 23,
                      "accent" if active else "muted")
            if active:
                y = center_y - box_h / 2 - 13 * self.scale
                draw.polygon([(round(x - 5 * self.scale), round(y - 6 * self.scale)),
                              (round(x + 5 * self.scale), round(y - 6 * self.scale)),
                              (round(x), round(y))], fill=PALETTE["accent"])
        if section == 2:
            pair = (2, 3) if time < 20 else (6, 7)
            y = center_y + (53 if self.portrait else 106) * self.scale
            left, right = centers[pair[0]] - box_w / 2, centers[pair[1]] + box_w / 2
            draw.line([(left, y), (right, y)], fill=PALETTE["accent"],
                      width=max(2, round(2 * self.scale)))
            self.text(draw, ((left + right) / 2, y + (16 if self.portrait else 31) * self.scale),
                      "LEFT DOUBLE" if time < 20 else "RIGHT DOUBLE",
                      10 if self.portrait else 20, color="accent", bold=True)

    def portrait_pattern(self, draw: ImageDraw.ImageDraw, center_y: float,
                         current_beat: int | None, section: int, time: float,
                         memory: bool, count_in: bool) -> None:
        # Four beats per row keep the actual lesson readable on a narrow picture.
        # These are instructional beat diagrams, not player controls.
        s = self.scale
        unit, box_w, box_h, row_gap = 86 * s, 70 * s, 56 * s, 90 * s
        double_pair = (2, 3) if section == 2 and time < 20 else (6, 7) if section == 2 else ()
        for index, hand in enumerate(PATTERN):
            row, column = divmod(index, 4)
            x = self.width / 2 + (column - 1.5) * unit
            y = center_y + row * row_gap
            active = current_beat == index and not count_in
            emphasized = index in double_pair
            rectangle = (round(x - box_w / 2), round(y - box_h / 2),
                         round(x + box_w / 2), round(y + box_h / 2))
            draw.rounded_rectangle(
                rectangle, radius=round(5 * s),
                fill=PALETTE["accent"] if active else None,
                outline=PALETTE["accent"] if active or emphasized else PALETTE["line"],
                width=max(1, round((2 if emphasized else 1) * s)))
            self.text(draw, (x, y - 1 * s), "·" if memory else hand, 36,
                      "accent_ink" if active else ("faint" if count_in else "ink"), bold=True)
            self.text(draw, (x, y + 44 * s), str(index + 1), 16,
                      color="accent" if active else "muted")
            if active:
                pointer_y = y - box_h / 2 - 7 * s
                draw.polygon([(round(x - 5 * s), round(pointer_y - 6 * s)),
                              (round(x + 5 * s), round(pointer_y - 6 * s)),
                              (round(x), round(pointer_y))], fill=PALETTE["accent"])
        if double_pair:
            row = double_pair[0] // 4
            left_column, right_column = double_pair[0] % 4, double_pair[1] % 4
            left = self.width / 2 + (left_column - 1.5) * unit - box_w / 2
            right = self.width / 2 + (right_column - 1.5) * unit + box_w / 2
            y = center_y + row * row_gap + box_h / 2 + 5 * s
            draw.line([(left, y), (right, y)], fill=PALETTE["accent"], width=max(2, round(2 * s)))

    def draw_landscape(self, draw, time, section, phase_title, instruction, event,
                       in_section, pulse, active_hand, current_beat, memory, count_in):
        s = self.scale
        self.text(draw, (96 * s, 68 * s), "TAP STUDY  /  40 SECOND LESSON", 23,
                  color="muted", anchor="lm")
        self.text(draw, (self.width - 96 * s, 68 * s), f"0{section + 1}  /  {phase_title.upper()}",
                  23, color="accent", anchor="rm")
        self.text(draw, (self.width / 2, 164 * s), "Catch the double.", 74, bold=True)
        self.text(draw, (self.width / 2, 244 * s), instruction, 32, color="muted")
        self.text(draw, (self.width / 2, 296 * s), "Use a tabletop, not the screen.",
                  22, color="muted")
        self.hand_diagram(draw, self.width * 0.34, 479 * s, 131 * s,
                          "L", active_hand == "L", pulse)
        self.hand_diagram(draw, self.width * 0.66, 479 * s, 131 * s,
                          "R", active_hand == "R", pulse)
        if count_in:
            number = str(event.beat + 1) if in_section and event.kind == "count-in" else "–"
            self.text(draw, (self.width / 2, 466 * s), number, 70,
                      color="accent", bold=True)
            self.text(draw, (self.width / 2, 526 * s), "COUNT IN", 19, color="muted")
        elif memory:
            self.text(draw, (self.width / 2, 473 * s), "YOUR", 23, color="accent", bold=True)
            self.text(draw, (self.width / 2, 510 * s), "TURN", 23, color="accent", bold=True)
        else:
            self.text(draw, (self.width / 2, 477 * s), "+", 34, color="faint")
        self.pattern_row(draw, 785 * s, current_beat, section, time, memory, count_in)
        # Keep the bottom150px clear for the player's native captions.

    def draw_portrait(self, draw, time, section, phase_title, instruction, event,
                      in_section, pulse, active_hand, current_beat, memory, count_in):
        s = self.scale
        self.text(draw, (28 * s, 32 * s), "TAP STUDY", 11, color="muted", anchor="lm")
        self.text(draw, (self.width - 28 * s, 32 * s), f"0{section + 1} / {phase_title}",
                  11, color="accent", anchor="rm")
        self.text(draw, (self.width / 2, 88 * s), "Catch the double.", 36, bold=True)
        self.wrapped(draw, self.width / 2, 148 * s, instruction, 17, self.width - 60 * s)
        self.text(draw, (self.width / 2, 206 * s), "Use a tabletop, not the screen.",
                  12, color="muted")
        self.hand_diagram(draw, self.width * 0.265, 317 * s, 66 * s,
                          "L", active_hand == "L", pulse)
        self.hand_diagram(draw, self.width * 0.735, 317 * s, 66 * s,
                          "R", active_hand == "R", pulse)
        if count_in:
            number = str(event.beat + 1) if in_section and event.kind == "count-in" else "–"
            self.text(draw, (self.width / 2, 315 * s), number, 35, color="accent", bold=True)
            self.text(draw, (self.width / 2, 354 * s), "COUNT", 10, color="muted")
        elif memory:
            self.text(draw, (self.width / 2, 307 * s), "YOUR", 10, color="accent", bold=True)
            self.text(draw, (self.width / 2, 328 * s), "TURN", 10, color="accent", bold=True)
        else:
            self.text(draw, (self.width / 2, 315 * s), "+", 20, color="faint")
        sequence_label = ("LEFT DOUBLE · BEATS 3–4" if time < 20 else "RIGHT DOUBLE · BEATS 7–8") \
            if section == 2 else "EIGHT TAPS · EVEN SPACING"
        self.text(draw, (self.width / 2, 446 * s), sequence_label, 12,
                  color="muted", bold=True)
        self.pattern_row(draw, 496 * s, current_beat, section, time, memory, count_in)
        # The lower120px stay clear for native captions on narrow video.


def write_click_audio(path: Path) -> dict:
    audio = np.zeros((DURATION * SAMPLE_RATE, 2), dtype=np.float32)
    for event in EVENTS:
        duration = 0.065 if event.kind == "tap" else 0.045
        count = round(duration * SAMPLE_RATE)
        sample_time = np.arange(count, dtype=np.float32) / SAMPLE_RATE
        frequency = 540.0 if event.hand == "L" else 820.0 if event.hand == "R" else 330.0
        envelope = np.exp(-sample_time * (85 if event.kind == "tap" else 115))
        envelope *= np.minimum(1.0, sample_time / 0.0015)
        waveform = (np.sin(2 * np.pi * frequency * sample_time)
                    + 0.20 * np.sin(2 * np.pi * frequency * 2.17 * sample_time)) * envelope
        gain = 0.48 if event.kind == "tap" else 0.22
        pan = -0.65 if event.hand == "L" else 0.65 if event.hand == "R" else 0.0
        angle = (pan + 1.0) * math.pi / 4
        stereo = waveform[:, None] * np.array([math.cos(angle), math.sin(angle)], dtype=np.float32)
        start = round(event.time * SAMPLE_RATE)
        end = min(len(audio), start + count)
        audio[start:end] += stereo[:end - start] * gain
    peak = float(np.max(np.abs(audio)))
    if not math.isfinite(peak) or peak >= 0.99:
        raise RuntimeError("Audio exceeds intended headroom")
    pcm = np.round(np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as output:
        output.setnchannels(2)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        output.writeframes(pcm.tobytes())
    return {"sample_rate": SAMPLE_RATE, "channels": 2, "peak_linear": peak,
            "audio": "Original synthesized clicks; left540Hz, right820Hz, neutral330Hz. No music.",
            "event_times": [event.__dict__ for event in EVENTS]}


def write_video(scene: LessonScene, fps: int, silent: Path, final: Path, audio: Path,
                ffmpeg: str) -> None:
    command = [ffmpeg, "-nostdin", "-n", "-f", "rawvideo", "-vcodec", "rawvideo",
               "-pix_fmt", "rgb24", "-s", f"{scene.width}x{scene.height}", "-r", str(fps),
               "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(silent)]
    log_path = silent.with_suffix(".encode.log")
    with log_path.open("x", encoding="utf-8") as log:
        child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
        try:
            assert child.stdin is not None
            for number in range(DURATION * fps):
                if number % (fps * 8) == 0:
                    print(f"Rendering {scene.width}x{scene.height}: {number // fps}/{DURATION}s", flush=True)
                frame = scene.frame(number / fps)
                child.stdin.write(frame.tobytes())
            child.stdin.close()
            result = child.wait()
            if result:
                raise RuntimeError(f"ffmpeg frame encode failed ({result}); retain {log_path.name}")
        except BaseException:
            # Only this captured child is terminated; all partial outputs are retained.
            if child.stdin is not None and not child.stdin.closed:
                try:
                    child.stdin.close()
                except OSError:
                    pass
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=10)
            raise
    mux_log = final.with_suffix(".mux.log")
    with mux_log.open("x", encoding="utf-8") as log:
        result = subprocess.run([ffmpeg, "-nostdin", "-n", "-i", str(silent), "-i", str(audio),
                                 "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                                 "-b:a", "160k", "-t", str(DURATION), "-movflags", "+faststart",
                                 str(final)], stdout=log, stderr=log, check=False)
    if result.returncode:
        raise RuntimeError(f"ffmpeg audio mux failed ({result.returncode}); retain {mux_log.name}")


def vtt_time(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02}.{millis:03}"


def write_vtt(path: Path, cues: list[tuple[float, float, str]]) -> None:
    previous_end = -1.0
    lines = ["WEBVTT", ""]
    for number, (start, end, text) in enumerate(cues, 1):
        if not (0 <= start < end <= DURATION) or start < previous_end:
            raise ValueError("Invalid or overlapping WebVTT cue")
        lines.extend([str(number), f"{vtt_time(start)} --> {vtt_time(end)}", text, ""])
        previous_end = end
    path.write_text("\n".join(lines), encoding="utf-8")


def prepare_output(raw_path: Path) -> Path:
    path = raw_path.expanduser().absolute()
    for existing in [path, *path.parents]:
        if existing.exists() and (existing.is_symlink() or
                bool(getattr(existing.lstat(), "st_file_attributes", 0) & 0x400)):
            raise ValueError("Output path must not pass through a symlink/reparse point")
    if path.exists():
        if not path.is_dir() or any(path.iterdir()):
            raise ValueError("Use a new or empty output directory; never overwrite retained media")
    else:
        path.mkdir(parents=True, exist_ok=False)
    return path.resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--fps", type=int, choices=(24, 30), default=30)
    parser.add_argument("--portrait-width", type=int, choices=(432, 720), default=432)
    args = parser.parse_args()
    height = args.width * 9 // 16
    if not (960 <= args.width <= 1920) or args.width % 32 or height % 2:
        parser.error("Landscape width must be 960–1920, divisible by 32, with an even 16:9 height")
    output = prepare_output(args.output)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    audio = output / "clicks.wav"
    audio_info = write_click_audio(audio)
    landscape = LessonScene(args.width, height)
    portrait_height = args.portrait_width * 16 // 9
    portrait = LessonScene(args.portrait_width, portrait_height)
    write_video(landscape, args.fps, output / "eight-tap-silent.mp4",
                output / "eight-tap.mp4", audio, ffmpeg)
    write_video(portrait, args.fps, output / "eight-tap-portrait-silent.mp4",
                output / "eight-tap-portrait.mp4", audio, ffmpeg)
    landscape.frame(0.0).save(output / "poster.jpg", quality=94, subsampling=0)
    portrait.frame(0.0).save(output / "portrait-poster.jpg", quality=94, subsampling=0)
    chapter_cues = [(start, PHASES[index + 1][0] - .05 if index + 1 < len(PHASES) else DURATION,
                     title) for index, (start, title, _) in enumerate(PHASES)]
    write_vtt(output / "chapters.vtt", chapter_cues)
    caption_cues = [
        (0, 1.95, "Use two hands on a tabletop. Count in and listen first."),
        (2, 5.95, "Listen: left, right, left, left, right, left, right, right."),
        (6, 7.95, "One pattern takes four seconds. Keep the gaps equal."),
        (8, 11.95, "Follow the highlighted hand: L R L L R L R R."),
        (12, 15.95, "One tap every half second. Keep a steady pace."),
        (16, 19.95, "Catch the left double: L L on beats three and four."),
        (20, 23.95, "Catch the right double: R R on beats seven and eight."),
        (24, 27.95, "Play along: L R L L R L R R."),
        (28, 31.95, "Keep the same spacing, including the doubles."),
        (32, 35.95, "Your turn. One guided round, then try it from memory."),
        (36, 40, "No hand hints this round. Keep the eight-tap pattern."),
    ]
    write_vtt(output / "captions-en.vtt", caption_cues)
    license_text = ("Original SIGHTLINE instructional media — CC0 1.0 Universal\n\n"
                    "Procedural diagrams, synthesized click audio, posters and VTT text are dedicated to the "
                    "public domain under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/\n"
                    "No third-party footage, music, image files or font files are distributed. Installed system "
                    "sans-serif fonts are rasterized into the rendered instruction. No claim is made that the "
                    "eight-tap sequence itself was invented or that a named musical technique is taught.\n"
                    "The media is instructional content, never a mockup of player behavior.\n")
    (output / "MEDIA-LICENSE.txt").write_text(license_text, encoding="utf-8")
    publish_files = ["eight-tap.mp4", "eight-tap-portrait.mp4", "poster.jpg", "portrait-poster.jpg",
                     "chapters.vtt", "captions-en.vtt", "MEDIA-LICENSE.txt"]
    manifest = {
        "title": "Catch the double — an eight-tap study",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "license": "CC0-1.0",
        "source_license": "Apache-2.0",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "duration_seconds": DURATION,
        "pattern": list(PATTERN),
        "fps": args.fps,
        "landscape": {"width": args.width, "height": height},
        "portrait": {"width": args.portrait_width, "height": portrait_height},
        "content": "Original learnable hand-tap diagram, not player controls or a playback mockup.",
        "claim_limit": "No claim of inventing the tap sequence, musical pedagogy certification, or measured learning benefit.",
        "cue_timing": "Intended click/visual events share timestamps. Actual encoded playback still needs independent QA.",
        "caption_gap_seconds": .05,
        "audio": audio_info,
        "files": [{"file": name, "bytes": (output / name).stat().st_size,
                   "sha256": hashlib.sha256((output / name).read_bytes()).hexdigest()} for name in publish_files],
        "retained_intermediates": ["clicks.wav", "eight-tap-silent.mp4", "eight-tap-portrait-silent.mp4",
                                   "eight-tap-silent.encode.log", "eight-tap-portrait-silent.encode.log",
                                   "eight-tap.mux.log", "eight-tap-portrait.mux.log"],
    }
    (output / "media-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "duration_seconds": DURATION,
                      "files": publish_files + ["media-manifest.json"],
                      "product_or_sync_acceptance": False}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Media generation stopped; partial outputs retained: {type(error).__name__}: {error}", file=sys.stderr)
        raise
