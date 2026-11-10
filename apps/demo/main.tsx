import { createRoot } from 'react-dom/client';
import { useState, type CSSProperties } from 'react';
import { I18nProvider } from '@videojs/react/i18n';
import { Video } from '@videojs/react/video';
import { SightlinePlayer } from '../../src/player';
import { VideoSkin } from '../../src/video/skin';
import './page.css';

const sources = {
  lesson: { src: 'practice/eight-tap.mp4', poster: 'practice/poster.jpg', title: 'The eight-tap pattern', subtitle: 'A 40-second lesson for two hands', chapters: 'practice/chapters.vtt', captions: 'practice/captions-en.vtt' },
  portrait: { src: 'practice/eight-tap-portrait.mp4', poster: 'practice/portrait-poster.jpg', title: 'The eight-tap pattern', subtitle: 'The same lesson, in portrait', chapters: 'practice/chapters.vtt', captions: 'practice/captions-en.vtt' },
  film: { src: 'the-fold.mp4', poster: 'poster.jpg', title: 'The Fold', subtitle: 'An original motion study', chapters: 'chapters.vtt', captions: 'captions-en.vtt' },
  bare: { src: 'practice/eight-tap.mp4', poster: 'practice/poster.jpg', title: 'Just the moment', subtitle: 'Without chapters or captions', chapters: '', captions: '' },
  bright: { src: 'bright.mp4', poster: '', title: 'Light study', subtitle: 'Bright footage', chapters: '', captions: '' },
  dark: { src: 'dark.mp4', poster: '', title: 'Shadow study', subtitle: 'Dark footage', chapters: '', captions: '' },
  short: { src: 'short.mp4', poster: '', title: 'A brief moment', subtitle: 'A three-second video', chapters: '', captions: '' },
  error: { src: 'missing-video.mp4', poster: '', title: 'Unavailable source', subtitle: 'Error-state preview', chapters: '', captions: '' },
} as const;
type Source = keyof typeof sources;
const params = new URLSearchParams(location.search);
const view = params.get('view') || 'site';
const revision = import.meta.env.VITE_BUILD_SHA || 'development';
const revisionLabel = revision.includes('-dirty') ? 'working copy' : revision.slice(0, 7);
const code = `import { Video } from '@videojs/react/video';
import { SightlinePlayer, VideoSkin } from './sightline';

<SightlinePlayer>
  <VideoSkin title="Your next great moment">
    <Video src="/your-film.mp4" playsInline />
  </VideoSkin>
</SightlinePlayer>`;

function Mark() { return <span className="brand-mark" aria-hidden="true"><i /><i /></span>; }

function DemoPlayer({ compact = false }: { compact?: boolean }) {
  const requested = params.get('source');
  const [source, setSource] = useState<Source>(requested && requested in sources ? requested as Source : 'lesson');
  const [accent, setAccent] = useState('#d9ef9b');
  const [radius, setRadius] = useState('16');
  const selected = sources[source];
  return <div className={`demo-content ${compact ? 'is-compact' : ''}`}>
    {!compact && <div className="demo-tools"><span className="section-label">ONE INSTANCE. TWO WAYS IN.</span><label>Video <select aria-label="Demo video" value={source} onChange={event => setSource(event.currentTarget.value as Source)}><option value="lesson">Eight taps · landscape</option><option value="portrait">Eight taps · portrait</option><option value="film">The Fold · motion study</option><option value="bare">Without tracks</option><option value="bright">Bright footage</option><option value="dark">Dark footage</option><option value="short">Short video</option><option value="error">Unavailable source</option></select></label></div>}
    <div className="player-stage">
      <I18nProvider locale="en"><SightlinePlayer>
        <VideoSkin title={selected.title} subtitle={selected.subtitle} sourceKey={source} initialMode={params.get('mode') === 'practice' ? 'practice' : 'watch'} practiceDisabled={params.get('guard') === 'live'} style={{ '--media-accent-color': accent, '--media-border-radius': `${radius}px` } as CSSProperties}>
          <Video src={`./media/${selected.src}`} poster={selected.poster ? `./media/${selected.poster}` : undefined} preload="auto" playsInline crossOrigin="anonymous">
            {selected.chapters && <track key={`${source}-chapters`} kind="chapters" src={`./media/${selected.chapters}`} default />}
            {selected.captions && <track key={`${source}-captions`} kind="captions" src={`./media/${selected.captions}`} label="English" srcLang="en" default />}
          </Video>
        </VideoSkin>
      </SightlinePlayer></I18nProvider>
    </div>
    {!compact && <div className="player-note"><span><span className="note-dot" /> Original film, sound & captions · CC0</span><span>Try chapter 03. Slow it. Loop the double.</span></div>}
    {view === 'site' && <div className="brand-controls" aria-label="Brand customization"><span>Make it yours</span><fieldset><legend className="visually-hidden">Accent</legend>{[['#d9ef9b', 'Citron'], ['#bce2e9', 'Sky'], ['#f2c5a7', 'Clay']].map(([value, name]) => <button type="button" key={value} aria-label={`${name} accent`} aria-pressed={accent === value} style={{ backgroundColor: value }} onClick={() => setAccent(value)}>{accent === value ? '✓' : ''}</button>)}</fieldset><label>Corner radius <input aria-label="Corner radius" type="range" min="0" max="32" value={radius} onChange={event => setRadius(event.currentTarget.value)} /><output>{radius}px</output></label></div>}
  </div>;
}

function App() {
  if (view === 'mobile-showcase') return <main className="mobile-showcase"><div className="mobile-story"><a className="brand" href="?view=site"><Mark />SIGHTLINE</a><p className="eyebrow">SAME SKIN. A DIFFERENT PACE.</p><h1>One detail.<br />In your hands.</h1><p>A chapter opens below the picture.<br />Your pace and place stay with you.<br />A loop is always yours to stop.</p><span className="showcase-caption">Live responsive player · 390 CSS pixels</span></div><div className="phone-stage"><iframe title="SIGHTLINE mobile player" src="?view=player&source=portrait&mode=practice" /></div></main>;
  if (view === 'player') return <main className="player-only"><DemoPlayer compact /><span className="review-stamp">SIGHTLINE · VIDEO.JS V10 · {revisionLabel}</span></main>;
  if (view === 'close') return <main className="closing-view"><a className="brand" href="?view=site"><Mark />SIGHTLINE</a><h1>Watch the moment.<br /><em>Make it yours.</em></h1><p>Video.js v10 · Source-owned · Apache 2.0</p><span>Never cover the moment.</span><a href="?view=site">Try the working preview ↗</a><small>Review build {revisionLabel}</small></main>;
  return <>
    <header className="site-nav"><a className="brand" href="#"><Mark />SIGHTLINE<span className="version">GUIDE DECK</span></a><nav aria-label="Main"><a href="#player">Try the lesson</a><a href="#integrate">Use the skin ↗</a></nav><span className="preview-flag">REVIEW CANDIDATE</span></header>
    <main>
      <section className="hero" aria-labelledby="headline"><div><p className="eyebrow">CONTENT FIRST. PRACTICE READY.</p><h1 id="headline">Never cover<br />the <em>moment.</em></h1></div><div className="hero-copy"><p>Some moments deserve<br />more than one watch.</p><span>See the detail. Find your pace.<br />Make the movement yours.</span><a href="#player">Catch the double tap <span aria-hidden="true">↓</span></a></div></section>
      <section className="demo-section" id="player" aria-label="Try SIGHTLINE"><div className="section-intro"><span className="section-label">01 / A MOMENT TO MASTER</span><div><h2>Can you catch<br />the double?</h2><p>Eight taps. Two hands. One small detail that slips past.<br />Watch the whole pattern, then find the double in Practice.</p></div></div><DemoPlayer /></section>
      <section className="approach" id="approach"><span className="section-label">02 / TWO RAILS. ONE CLEAR PURPOSE.</span><div className="principles"><article><span className="principle-rails"><i /><i /></span><h2>The picture<br />stays yours.</h2><p>The controls have their own space. Captions stay in the picture, with nothing layered over them.</p></article><article><span className="principle-rails guide"><i /><i /></span><h2>One rail follows.<br />One rail guides.</h2><p>Playback above. Chapters and your exact A–B range below. A step has a name; a loop has a clear way out.</p></article><article><span className="principle-symbol">↗</span><h2>Watch once.<br />Make it yours.</h2><p>Go to the detail, slow the actual video, and repeat it. Switching mode keeps one media instance and your place.</p></article></div></section>
      <section className="integration" id="integrate"><span className="section-label">03 / SOURCE YOU OWN</span><div className="integration-grid"><div><h2>Your site.<br />Your sightline.</h2><p>Six small source files. Real Video.js v10 primitives.<br />Keep your React runtime, change the accent and radius,<br />and supply your own video and VTT.</p><a className="text-link" href="./README.html">Read the integration guide ↗</a><p className="token-list">--media-accent-color<br />--media-accent-text-color<br />--media-border-radius</p></div><div className="code-panel"><span>React + TypeScript / Video.js 10.3.0</span><pre><code>{code}</code></pre><p>Install the pinned Video.js packages in an existing React 18 or 19 app. The guide includes the complete i18n setup and minimal file list.</p></div></div></section>
      <aside className="access-note"><span aria-hidden="true">↹</span><p>Keyboard focus you can see. A loop you can stop.<br /><span>Calm motion on request. System colors when you need them.</span></p><a href="./README.html">Keyboard & integration ↗</a></aside>
    </main>
    <footer><a className="brand" href="#"><Mark />SIGHTLINE</a><span>Never cover the moment.</span><div><span>Video.js v10</span><a href="./LICENSE.txt">Apache 2.0</a><a href="./media/practice/MEDIA-LICENSE.txt">Original media · CC0</a></div></footer>
    <div className="candidate-note">Private review candidate · {revisionLabel} · Existing Contra entry and public demo are unchanged.</div>
  </>;
}
createRoot(document.getElementById('root')!).render(<App />);
