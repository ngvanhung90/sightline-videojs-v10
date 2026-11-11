# SIGHTLINE — Guide Deck review candidate

**AWAITING_OWNER_DESIGN_AND_RELEASE_APPROVAL.** This isolated branch does not authorize a Contra edit, social post, duplicate entry, public-repository main update or replacement of the existing demo.

SIGHTLINE keeps the picture clear and provides a deliberate practice layer: two time-correlated rails, named VTT chapters, direct rates and exact A–B intervals. Watch and Practice share one Video.js v10 native Video instance. An active loop has a visible stop action in either mode.

## Protected baseline

- Existing entry: https://contra.com/community/UTpczOTl-sightline-video-player-with-practice-controls
- Existing public demo: https://sightline-player.ng-van-hung90.chatgpt.site
- Existing source: https://github.com/ngvanhung90/sightline-videojs-v10
- Baseline code 59df9092687fa8c808937e89a23f1d23b1b07a8b; receipt documentation 455b8e0125cafc43bfe8d1e8ae50f55187b0b6de.

A fresh account audit found a social-completion gate: the saved entry is currently marked incomplete until its social-post URL is supplied. The earlier receipt proves a saved post, not final eligibility. The Owner-authorized support email asks Contra to confirm completion, editing and judging-version rules. No social completion or existing entry edit has been performed by this rescue branch.

## Run the isolated candidate

Node 24 LTS, npm and the committed lockfile are the reproducible baseline.

```sh
npm ci
npm run dev
npm run typecheck
npm run lint
npm run build
npm run build:workbench
```

The local candidate uses port 5174. Preview target (Owner-only, separate Site): https://sightline-owner-review.ng-van-hung90.chatgpt.site . Publication and runtime verification are reported separately in the Owner review package.

For the controlled Owner workstation, package/build/media/clone operations must use its reviewed storage producer; do not bypass host admission with the commands above. Ordinary consumers run these commands on their own host.

## Integrate only six files

Copy these paths into your application's `src/sightline/`, preserving the relative structure:

```text
index.ts
player.ts
video/skin.tsx
video/skin.css
video/icons.tsx
video/use-practice-loop.ts
```

Install `@videojs/react@10.3.0` and `@videojs/core@10.3.0` into an existing supported React 18 or 19 app. Keep the app's React runtime; the minimal skin needs no cn or scaffold helpers.

```tsx
import { I18nProvider } from '@videojs/react/i18n';
import { Video } from '@videojs/react/video';
import { SightlinePlayer, VideoSkin } from './sightline';

export function Film() {
  return (
    <I18nProvider locale="en">
      <SightlinePlayer>
        <VideoSkin title="Your film" sourceKey="film-01">
          <Video src="/film.mp4" playsInline crossOrigin="anonymous">
            <track kind="chapters" src="/chapters.vtt" default />
            <track kind="captions" src="/captions.vtt" srcLang="en" label="English" />
          </Video>
        </VideoSkin>
      </SightlinePlayer>
    </I18nProvider>
  );
}
```

Tracks are optional. WebVTT needs a valid MIME type and cross-origin assets need suitable CORS. Keep provider, skin and media mounted across mode changes; supply a fresh sourceKey when choosing another asset. This is client-side native-video support; other media adapters and SSR/Next hydration are not claimed.

Set `--media-accent-color`, `--media-accent-text-color`, `--media-border-radius` and `--media-font-family` on the skin. Choose accent/text colors together and test contrast.

## Practice behavior

Choose a chapter, set the real playback rate, then capture A and B from the current native time. B must be at least 0.25 seconds after A, within a currently seekable range. Point values include fractions, and the shared range readout shows duration and repeats. Reset/Stop loop is explicit and returns keyboard focus to the chapter trigger.

A–B requires a finite, seekable, on-demand native Video at least 0.25 seconds long. Live, unknown duration and other adapters keep it disabled. Source/range changes invalidate pending returns. A resolved seek is checked against the intended source and actual position before counting. Automatic returns suppress only their seek announcements; manual playback/rate/volume changes retain Video.js announcements. Actual screen-reader behavior must be tested, not inferred from the DOM.

## Original lesson and demonstration

The new 40-second lesson teaches `L R L L R L R R` as a reproducible tabletop exercise, with original diagrams and synchronized synthesized clicks. Chapter 03 highlights the doubles. The 16–20 second bar is a useful repeat range. The sequence is not claimed as an invention or a certified teaching method. No learning-speed or click-count improvement is claimed without measurement.

The generator is `scripts/generate_lesson.py`. The original render, intermediate WAV/silent videos and provenance are retained separately; only published assets are staged in `apps/demo/public/media/practice`. The illustrated hands, tap sequence diagrams, synthesized clicks and authored VTT are original CC0 work. Hand movement is an instructional illustration, not a recording of a person.

The second example (`?view=workshop`) uses the same skin with a different brand and real pen movement: **Handwriting Minuscule Alphabet**, by **Peter Unbehauen**, licensed [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/), [source on Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Handwriting_Minuscule_Alphabet.webm). Changes: a 32-second excerpt from 00:08, original audio removed, H.264 encode; no tempo change. Original author marks remain visible. This is an example integration, not a client endorsement. Attribution and hash provenance accompany the media in `apps/demo/public/media/handwriting`.

Code is Apache 2.0. The original lesson is CC0; the third-party calligraphy excerpt remains CC BY 3.0. No paid APIs, analytics, backend, external font downloads or user accounts are added.

## Verification and approval

Development checks are distinct from final locked-commit QA. The Owner package records browser/hardware/assistive-technology results individually, including NOT_RUN. No WCAG certification is claimed. The final recording must use only the locked rescue commit at native 1920×1080; old RC captures must not be mixed into it.

The final review package includes actual before/after captures, video, independent comparison and scoring, QA evidence, rule-update status and remaining pre-deadline actions. Existing live content and the saved Contra entry remain unchanged until explicit Owner design and release approval.

The demo chooses the authored portrait lesson on an initial narrow viewport when no source is requested. Resizing does not silently switch a playing source. The selector always exposes the chosen media. Watch/Practice keep the same media instance.
