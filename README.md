# SIGHTLINE — Never Cover the Moment

*A player that gets out of the way when you watch, and helps you master what you see.*

SIGHTLINE is a source-owned Video.js v10 skin for React and TypeScript. Its controls sit below the picture. Watch mode keeps the essentials close; Practice adds chapters, direct speed choices, and an A–B loop on the same media instance.

Two guide rails give the skin its identity: one shows playback progress, and the second marks chapters and the practice range. Both have a job. No backend, accounts, analytics service, or paid API is required.

- [Repository](https://github.com/ngvanhung90/sightline-videojs-v10) — public source; clean-clone checks passed.
- [Live demo](https://sightline-player.ng-van-hung90.chatgpt.site) — public playback verified without a sign-in gate.
- [Received Contra Challenge entry](https://contra.com/community/UTpczOTl-sightline-video-player-with-practice-controls) — official Submit entry confirmation retained in [the receipt](docs/SUBMISSION-RECEIPT.json).
- [Design and submission notes](docs/CONTRA-SUBMISSION.md)
- [Media sources and licenses](docs/MEDIA-SOURCES.md)

## Verified scope

Real Chrome checks exercised native playback, seek, volume/mute, fullscreen, captions, VTT chapters, mode preservation, direct rates, A–B repetition/reset, 320/360/768/1280px layouts, keyboard focus/Escape, forced colors, reduced motion and brand tokens. The selected-label contrast defect was fixed and visually retested; final VTT cue boundaries were verified without overlapping active captions. Touch was trusted Chrome emulation; a local live MediaStream and an invalid source tested loop guards.

Typecheck, lint, standalone and workbench builds passed. The public repository was independently cloned, installed with `npm ci`, typechecked, linted and built. Public page/media/VTT requests with no Cookie or Authorization succeeded, and native Chrome playback on production advanced. See [the scoped QA matrix](docs/QA-MATRIX.json). Safari, Firefox, physical handset and screen-reader testing have not run; no WCAG certification is claimed.

[Watch the 79-second walkthrough](https://sightline-player.ng-van-hung90.chatgpt.site/sightline-demo.mp4). This is an edited, silent recording of actual Chrome local/production operation at original timing; capture sampling varies. It demonstrates the product, and does not replace the QA evidence. Some earlier RC footage precedes the final caption cue-gap patch.

## Run locally

Use Node.js 24 LTS and npm. The lockfile is the reproducible dependency baseline. Video.js packages are pinned to **10.3.0**, with React and React DOM **19.3.1**.

```sh
git clone https://github.com/ngvanhung90/sightline-videojs-v10.git
cd sightline-videojs-v10
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://127.0.0.1:5173`. The demonstration assets belong in `apps/demo/public/media/`; the media guide describes regeneration.

```sh
npm run typecheck
npm run lint
npm run build
npm run preview
```

The main build is the standalone SIGHTLINE demonstration. The original CLI workbench is retained in `apps/preview/`; `npm run build:workbench` builds it separately with its additional preview settings. Third-party deployment scripts may request host sign-in; local development needs no hosting account.

## Add SIGHTLINE to your app

This repository distributes source rather than an npm skin package. Copy the complete `src/` directory into your React application, for example as `src/sightline/`. Public exports are in `src/index.ts`; the skin imports its own stylesheet. The retained scaffold helpers also need `cn@0.4.0` when copying the full source tree.

```sh
npm install @videojs/react@10.3.0 @videojs/core@10.3.0 react@19.3.1 react-dom@19.3.1 cn@0.4.0
```

```tsx
import { I18nProvider } from '@videojs/react/i18n';
import { Video } from '@videojs/react/video';
import { SightlinePlayer, VideoSkin } from './sightline';

export function Film() {
  return (
    <I18nProvider locale="en">
      <SightlinePlayer>
        <VideoSkin title="A closer look" sourceKey="film-01">
          <Video src="/film.mp4" playsInline crossOrigin="anonymous">
            <track kind="chapters" src="/chapters.vtt" default />
            <track kind="captions" src="/captions-en.vtt"
              srcLang="en" label="English" />
          </Video>
        </VideoSkin>
      </SightlinePlayer>
    </I18nProvider>
  );
}
```

Tracks are optional. Serve valid WebVTT as `text/vtt`; cross-origin video and tracks require suitable CORS headers. A video without chapters or captions retains essential playback controls, and the chapter panel explains how to create a practice range.

Keep the player, skin, and media mounted across mode changes. When selecting another asset, update `Video` and `sourceKey`; avoid a mode-dependent React `key` that remounts the media.

### Brand properties

Set these properties on `VideoSkin` through a class or an ancestor:

```css
.my-player {
  --media-accent-color: #bce2e9;
  --media-accent-text-color: #172117;
  --media-border-radius: 12px;
  --media-font-family: system-ui, sans-serif;
}
```

Use `<VideoSkin className="my-player">`. Choose accent and text colors together, then check selected controls and focus contrast. Internal `--sl-*` properties in `src/video/skin.css` define surfaces and motion.

## Watch and Practice

Watch has play/pause, seek, time, volume/mute, captions, and fullscreen through real Video.js React primitives. Picture and controls share the fullscreen container while occupying separate layout regions.

Practice uses the same media. VTT chapters seek to their exact start times. Speed choices are `0.75×`, `1×`, `1.25×`, `1.5×`, and `2×`. Switching modes does not request a media reload or change the playback rate or subtitle selection.

1. Seek to a detail and choose **Set A**.
2. Play forward and choose **Set B**, more than 0.25 seconds after A.
3. The second rail shows the range; playback returns to A at B.
4. Choose **Reset loop** to restore the full video.

Choosing a chapter, seeking outside the range, or changing source clears the loop. Setting A again clears the old B. Loop controls require a finite, on-demand source and are disabled for live or unknown-duration video. Browser scheduling affects loop precision; this is a practice aid rather than a frame-accurate editor.

## Keyboard and accessibility

The implementation includes labels, visible focus, status announcements, reduced-motion CSS, and forced-color styling. Controls follow DOM order. Narrow players use a compact chapter panel below the picture and a mute control in place of the volume slider.

| Key | Action within the player |
| --- | --- |
| Tab / Shift+Tab | Move between controls |
| Enter / Space on a button | Activate the focused control |
| Space or K | Toggle playback |
| Left / Right | Seek five seconds |
| Up / Down | Adjust volume |
| M | Toggle mute |
| C | Toggle captions |
| F | Toggle fullscreen |
| Escape | Close chapters and return focus to the trigger |

Sliders also retain native keyboard behavior when focused. Fullscreen and volume availability depend on the browser/device. Implementation intent is not a test result or a conformance certification.

## Verification status

The Owner matrix is Q01–Q22. Executed checks have retained evidence; local synthetic and touch-emulation scopes are identified. Contra confirmed receipt through the official Challenge submission flow; see the separate submission receipt. This is not an award or judging outcome. Four actual interface captures are in `docs/assets/`; detailed native-state evidence is retained with the Owner deliverables.

## Source map and license

- `src/index.ts`: public exports.
- `src/player.ts`: typed video player with stream-type feature.
- `src/video/skin.tsx` and `skin.css`: interface, practice behavior, tokens, and responsive styles.
- `apps/demo/`: standalone demo; `apps/preview/`: retained CLI workbench.
- `scripts/generate_media.py`: original film and synthesized audio generator.
- `skin.json`: official CLI scaffold provenance.

Source is licensed under [Apache 2.0](LICENSE). Original generated footage, audio, posters, and VTT text use CC0 1.0; see [provenance](docs/MEDIA-SOURCES.md). Preserve upstream notices. SIGHTLINE began with the official Video.js 10.3.0 React/CSS Scaffold and uses the new `@videojs/*` architecture, without the legacy v8 initializer or plugin API. This independent entry claims no official selection or endorsement.
