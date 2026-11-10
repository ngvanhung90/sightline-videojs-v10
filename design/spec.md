# SIGHTLINE design specification

Locked 2026-11-10 from the Owner brief. Execution details derived below.

Content-first / Practice-ready. One mounted Video.js v10 React media instance, one source-owned skin based on official CLI Scaffold. No backend, accounts or external analytics.

Derived palette: ink #171c1b, warm off-white #f1f3e9, muted sage #b1bab5, adjustable pale citron accent #d9ef9b. System typography. Original 24px outline icon family, 1.7px rounded strokes. No borrowed competitor UI or fonts.

Picture first. Below: media title + Watch/Practice segmented control; playback rail and functional chapter/loop guide rail; play, back five, time, volume/mute, captions, fullscreen. Solid surfaces isolate text from bright/dark footage. Captions stay inside picture, controls outside it.

Practice adds direct speeds 0.75/1/1.25/1.5/2; chapter rail sourced from valid VTT; A/B capture and reset. Desktop chapters four columns, compact two columns, mobile inline sheet below picture. No blocking modal or focus trap. Escape closes chapters and restores trigger focus. A–B requires positive finite native duration AND on-demand streamType; source changes and external seeks clear stale loops.

Player container queries, 44px primary targets, thumb-friendly transport row. Native fullscreen includes picture and deck. Public accent/radius/font tokens. Visible focus; semantic labels; state with text and shape; polite announcements; reduced-motion and forced-colors.

Demo is a standalone project showcase alongside the retained official workbench. Generated original paper-fold footage has its own portrait composition, chapters and captions. Four actual interface screenshots and a 75–90 second real UI recording are deliverables after verified operation.
