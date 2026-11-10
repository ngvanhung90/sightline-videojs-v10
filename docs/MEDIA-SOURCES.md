# Media and source provenance

## Original demonstration film

**The Fold — a study in motion** is original procedural artwork created for SIGHTLINE by `scripts/generate_media.py`. A geometric sheet of cream paper rests on a textured slate/sage tabletop. Four chapters match visible actions: Observe, Align the edges, Make the fold, and Follow through.

Pillow and NumPy generate the animation. There are no downloaded footage, photographs, stock images, models, or external creative assets. This is content played by the demo, not a simulation or recording of player functionality.

Landscape and portrait versions include original synthesized audio: sustained sine harmonics with fades, encoded from stereo 48kHz PCM to AAC. No song, voice, recording, sample library, or third-party audio is used. Bright/dark/short diagnostics are silent.

## Asset inventory

Paths are relative to the generated media directory, normally `apps/demo/public/media/`. The generated manifest records actual byte sizes after execution.

| Files | Purpose | License |
| --- | --- | --- |
| `the-fold.mp4` | 32s landscape film, 16:9, original ambient audio | CC0-1.0 |
| `the-fold-portrait.mp4` | 16s portrait composition, 9:16, original ambient audio | CC0-1.0 |
| `bright.mp4`, `dark.mp4` | 5s bright/dark diagnostics | CC0-1.0 |
| `short.mp4` | 3s short-video diagnostic | CC0-1.0 |
| `poster.jpg`, `portrait-poster.jpg` | Generated frames of each composition | CC0-1.0 |
| `chapters.vtt`, `portrait-chapters.vtt` | Four cues matching each film's timing | CC0-1.0 |
| `captions-en.vtt`, `portrait-captions-en.vtt` | Original instructional text matched to visible motion | CC0-1.0 |
| `the-fold-silent.mp4`, `the-fold-portrait-silent.mp4` | Retained films before audio muxing | CC0-1.0 |
| `the-fold-ambient.wav`, `the-fold-portrait-ambient.wav` | Retained synthesized PCM audio | CC0-1.0 |
| `MEDIA-LICENSE.txt`, `media-manifest.json` | Generated provenance and media metadata | Documentation |

Original output media and VTT text are dedicated under [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/). Attribution is welcome but not required by that dedication. The Python generator source is Apache 2.0 with the rest of the project's source.

The generator rasterizes installed system fonts into frames. It neither downloads fonts nor redistributes font binaries. Another environment uses an available listed font or Pillow's default font.

## Reproduction

Install Pillow, NumPy, and imageio-ffmpeg in your own Python environment, then run:

```sh
python -B scripts/generate_media.py --output /absolute/path/to/fresh-media --width 960 --fps 24
```

`--width 1280` produces 1280×720 landscape; portrait output is 432×768. The generator resolves ffmpeg through imageio-ffmpeg, refuses to overwrite named outputs, and retains silent MP4 and WAV intermediates without automatic cleanup.

On the Owner's controlled host, rendering must use its reviewed storage-admission producer. Generating media alone is not evidence that playback, volume, captions, chapters, or E2E passed.

## Player source and scaffold

SIGHTLINE started from the official `@videojs/cli@10.3.0` React/CSS Scaffold. Its source is licensed under [Apache 2.0](../LICENSE). Preserve upstream notices when redistributing. Third-party package licenses remain their respective authors' licenses.

- [Video.js](https://videojs.org/)
- [Official skin guide](https://videojs.org/docs/framework/react/guides/build-your-own-skin)
- [Video.js skills](https://github.com/videojs/skills)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

The retained CLI workbench is separate from the standalone demo. Its original external demo footage must not be described as SIGHTLINE-owned or as a Mux bonus asset belonging to this entry. The main demo is intended to use only the original assets above.

No interface or footage assets from other entries are used. No official catalog inclusion, endorsement, or contest award is claimed.
