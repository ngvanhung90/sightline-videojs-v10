# SIGHTLINE — Never Cover the Moment

**Submitted through the official Challenge form.** Contra returned “Entry Submitted” and “Your entry has been submitted”. See SUBMISSION-RECEIPT.json for the entry URL and evidence; no award or judging outcome is claimed.

## Entry fields

| Field | Value |
| --- | --- |
| Framework | React + TypeScript; Video.js v10.3.0 |
| Source license | Apache License 2.0 |
| Repository target | https://github.com/ngvanhung90/sightline-videojs-v10 — public, clean-clone checks passed |
| Demo target | https://sightline-player.ng-van-hung90.chatgpt.site — public playback and unauthenticated HTTP verified |
| Mux bonus | Not claimed; no qualifying own-asset playback ID verified |
| Live-site bonus | Not claimed until the real live site is verified and entered |
| Accepted submission URL | https://contra.com/community/UTpczOTl-sightline-video-player-with-practice-controls |

## Short description

Watch the moment. Don't cover it. SIGHTLINE places the controls below the picture, then opens a focused Practice mode when you want to look closer. Two guide rails make playback and repetition legible: one follows the video, and the other marks chapters and your A–B range. Switch modes without replacing the media instance; your place, pace, and captions stay with you.

## Design thinking

The most important part of a player is the picture. A beautiful control bar can still cover the detail someone came to see, compete with captions, or make a simple repeat action feel like work. SIGHTLINE gives the image room and keeps the essential controls on a stable surface beneath it.

A second need appears when watching becomes learning: finding a step, slowing a movement, and trying it again. Practice adds that layer without turning the player into a course platform or an editing timeline. Chapters, five direct speed choices, and two loop points help the viewer return to the detail.

Dual Guide Rails is the visual idea behind the skin. The first rail is playback progress. The second carries chapter boundaries and the practice range. The marks correspond to real time and actions. Restrained citron, quiet surfaces, crisp icons, and tabular time keep the interface clear across changing footage.

Video.js v10 makes this structure practical. The source-owned skin composes real player primitives and custom practice controls, connected to one player store and media instance. Developers can copy the source into their own applications and adapt both the interface and its behavior.

## Installation and customization

Copy `src/` into a React application, install `@videojs/react@10.3.0` `@videojs/core@10.3.0`, and `cn@0.4.0`, and import `SightlinePlayer` and `VideoSkin` from the copied directory's index. Place a Video.js `Video` inside the skin. VTT chapters and captions are optional.

Brand properties are `--media-accent-color`, `--media-accent-text-color`, `--media-border-radius`, and `--media-font-family`. The repository README contains a complete integration example and local setup instructions.

## Accessibility statement — complete after testing

Real Chrome checks have exercised keyboard operation and focus return, native captions and fullscreen, chapter seeking, real A–B repetition, responsive player widths from 320 to 1280px, brand tokens, reduced motion and forced colors. Trusted touch events were emulated in Chrome; physical handset, screen-reader, Safari and Firefox testing have not run. This is scoped test evidence, not WCAG certification.

The selected-label forced-colors defect was fixed and visually retested. Final caption cue boundaries were verified through native active cues without overlap.

See QA-MATRIX.json for retained evidence and remaining public/clean-clone/submission checks. The 78.9-second silent walkthrough uses actual Chrome captures at original timing; it is a product demonstration, separate from test evidence.

## Attachments — actual interface captures

| Attachment | Capture needed |
| --- | --- |
| Screenshot 1 | Desktop Watch, playing footage/captions, controls below picture |
| Screenshot 2 | Desktop Practice, chapters, selected speed, active A–B range |
| Screenshot 3 | Mobile 360px, portrait video and usable playback controls |
| Screenshot 4 | Mobile chapters or visible keyboard focus from the running player |
| Demo recording | 75–90 seconds of actual Watch/Practice/mobile/accessibility operation |

The film inside the player, “The Fold — a study in motion,” is original procedural content. It is not evidence of player behavior. Screenshots and the recording must capture the running interface.

## Recording sequence

| Time | Actual interface to capture |
| --- | --- |
| 0–7s | Playing footage and captions; “Watch the moment. Don't cover it.” |
| 7–20s | Watch controls, captions, seek, fullscreen |
| 20–36s | Switch to Practice, select a chapter, show continuous media state |
| 36–53s | Choose 0.75×/1.5×, capture A/B, show real repetition, reset |
| 53–67s | 360px, 9:16 media, touch and compact chapter panel |
| 67–79s | Keyboard focus, reduced motion, branding, bright/dark footage |
| 79–90s | SIGHTLINE, Video.js v10, verified source/demo URLs, closing message |

## Before final submission

- Verify source and demo from a signed-out session.
- Verify Apache 2.0 source licensing and attribution.
- Attach actual captures and the completed recording.
- Use the official Challenge join and submission flow.
- Save the accepted entry URL and confirmation screen.
- Set `SUBMITTED_TO_CHALLENGE=PASS` only when Contra confirms receipt.

The public Guidelines show **November 16, 2026, 11:59pm PST**, equivalent to **November 17, 2026, 14:59 in Vietnam**. Verify the live account flow before relying on this deadline. [Official Guidelines](https://contra.com/community/topic/videojsskinschallenge/guidelines).
