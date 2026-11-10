import { createRoot } from 'react-dom/client';
import { useState, type CSSProperties } from 'react';
import { I18nProvider } from '@videojs/react/i18n';
import { Video } from '@videojs/react/video';
import { SightlinePlayer } from '../../src/player';
import { VideoSkin } from '../../src/video/skin';
import './page.css';

const sources = {
 landscape: { src: 'the-fold.mp4', poster: 'poster.jpg', title: 'The Fold', subtitle: 'A study in motion · 00:32', chapters: 'chapters.vtt', captions: 'captions-en.vtt' },
 portrait: { src: 'the-fold-portrait.mp4', poster: 'portrait-poster.jpg', title: 'The Fold, vertical', subtitle: 'A different point of view · 00:16', chapters: 'portrait-chapters.vtt', captions: 'portrait-captions-en.vtt' },
 bare: { src: 'the-fold.mp4', poster: 'poster.jpg', title: 'Just the moment', subtitle: 'No chapters. No captions.', chapters: '', captions: '' },
 bright: { src: 'bright.mp4', poster: 'poster.jpg', title: 'Light study', subtitle: 'Bright footage · 00:05', chapters: '', captions: '' },
 dark: { src: 'dark.mp4', poster: 'poster.jpg', title: 'Shadow study', subtitle: 'Dark footage · 00:05', chapters: '', captions: '' },
 short: { src: 'short.mp4', poster: 'poster.jpg', title: 'A brief moment', subtitle: 'Short video · 00:03', chapters: '', captions: '' },
 error: { src: 'missing-video.mp4', poster: '', title: 'Connection study', subtitle: 'Intentional error-state preview', chapters: '', captions: '' },
} as const;
type Source = keyof typeof sources;
const code = `import { Video } from '@videojs/react/video';\nimport { SightlinePlayer, VideoSkin } from './sightline';\n\n<SightlinePlayer>\n  <VideoSkin title="Your next great moment">\n    <Video src="/your-video.mp4" playsInline />\n  </VideoSkin>\n</SightlinePlayer>`;
function App() {
 const params = new URLSearchParams(location.search);
 const requested = params.get('source');
 const [source, setSource] = useState<Source>(requested && requested in sources ? requested as Source : 'landscape');
 const [accent, setAccent] = useState('#d9ef9b'); const [radius, setRadius] = useState('18');
 const [copied, setCopied] = useState(false);
 const selected = sources[source];
 return <>
  <header className="site-nav"><a className="brand" href="#"><span className="brand-icon" aria-hidden="true"><i/><i/></span>SIGHTLINE<span className="version">v1.0</span></a><nav aria-label="Main"><a href="#approach">The idea</a><a href="#integrate">Make it yours <span aria-hidden="true">↗</span></a></nav><span className="nav-meta">VIDEO.JS V10<span>OPEN SOURCE / APACHE 2.0</span></span></header>
  <main>
   <section className="hero" aria-labelledby="headline"><div><p className="eyebrow"><span/>CONTENT FIRST. PRACTICE READY.</p><h1 id="headline">Never cover<br/>the <em>moment.</em></h1></div><div className="hero-copy"><p>A player that gets out of the way<br className="desktop-break"/> when you watch. And helps you<br className="desktop-break"/> master what you see.</p><a href="#player" className="jump-link">Meet your new point of view <span aria-hidden="true">↓</span></a></div></section>
   <section className="demo-section" id="player" aria-label="Try SIGHTLINE">
    <div className="section-meta"><span>01 <i/> THE PLAYER</span><label>Try a different view <select aria-label="Demo video" value={source} onChange={e => setSource(e.currentTarget.value as Source)}><option value="landscape">Landscape · 16:9</option><option value="portrait">Portrait · 9:16</option><option value="bare">Without tracks</option><option value="bright">Bright footage</option><option value="dark">Dark footage</option><option value="short">Short video</option><option value="error">Error state</option></select></label></div>
    <div className={`player-stage ${source === 'portrait' ? 'is-portrait' : ''}`}>
     <I18nProvider locale="en"><SightlinePlayer>
      <VideoSkin title={selected.title} subtitle={selected.subtitle} sourceKey={source} initialMode={params.get('mode') === 'practice' ? 'practice' : 'watch'} practiceDisabled={params.get('guard') === 'live'} style={{ '--media-accent-color': accent, '--media-border-radius': `${radius}px` } as CSSProperties}>
       <Video src={`./media/${selected.src}`} poster={selected.poster ? `./media/${selected.poster}` : undefined} preload="auto" playsInline crossOrigin="anonymous">
        {selected.chapters && <track key={`${source}-chapters`} kind="chapters" src={`./media/${selected.chapters}`} default />}
        {selected.captions && <track key={`${source}-captions`} kind="captions" label="English" srcLang="en" src={`./media/${selected.captions}`} default />}
       </Video>
      </VideoSkin>
     </SightlinePlayer></I18nProvider>
    </div>
    <div className="demo-caption"><span><span className="tiny-rails" aria-hidden="true">〓</span> ONE MOMENT. TWO WAYS IN.</span><p>Try Practice. The video keeps its place.</p></div>
   </section>
   <section className="approach" id="approach"><div className="section-meta"><span>02 <i/> A CLEARER WAY TO WATCH</span></div><div className="approach-grid"><div className="approach-lead"><h2>Less in the way.<br/>More within reach.</h2><p>The picture is the point. SIGHTLINE gives it room to breathe, with a second layer of control when you want to look closer.</p></div><div className="principles"><article><span>01</span><div><h3>The frame stays yours.</h3><p>Controls sit below the picture. Captions have their own space. Bright or dark, the moment stays clear.</p></div></article><article><span>02</span><div><h3>Two rails. One clear purpose.</h3><p>One follows the story. The other marks chapters and your A–B range. Watch the whole, or repeat the detail.</p></div></article><article><span>03</span><div><h3>A change of mode. No interruption.</h3><p>Watch to Practice on the same media instance. Your place, pace and captions come with you.</p></div></article></div></div></section>
   <section className="integration" id="integrate"><div className="section-meta"><span>03 <i/> MAKE IT YOURS</span><span>REACT + TYPESCRIPT</span></div><div className="integration-grid"><div><h2>Your site.<br/>Your sightline.</h2><p>Source you own. Video.js primitives underneath. A few public CSS properties make it feel at home.</p><div className="brand-controls"><fieldset><legend>Accent</legend>{[['#d9ef9b','Citron'],['#bce2e9','Sky'],['#f2c5a7','Clay']].map(([color,name])=><button type="button" key={color} className="swatch" style={{ background:color }} aria-label={`${name} accent`} aria-pressed={accent===color} onClick={()=>setAccent(color)}>{accent===color?'✓':''}</button>)}</fieldset><label className="radius-control">Corner radius <input aria-label="Corner radius" type="range" min="0" max="32" value={radius} onChange={e=>setRadius(e.currentTarget.value)}/><output>{radius}px</output></label></div><p className="property-hint"><code>--media-accent-color</code><br/><code>--media-border-radius</code></p></div><div className="code-panel"><div><span>A small beginning.</span><button type="button" onClick={()=>{void navigator.clipboard.writeText(code).then(()=>{setCopied(true);setTimeout(()=>setCopied(false),2000);});}}>{copied?'Copied ✓':'Copy code ↗'}</button></div><pre><code>{code}</code></pre><p>Copy <code>src/</code> into your React app. Install <code>@videojs/react@10.3.0</code> and <code>@videojs/core@10.3.0</code>.</p></div></div></section>
   <aside className="access-note"><span className="access-symbol" aria-hidden="true">↹</span><p>Space to pause. Arrows to seek. C for captions.<br/><span>Visible focus, generous targets, and calm motion on request.</span></p><a href="./README.html">Read the guide ↗</a></aside>
  </main>
  <footer><a className="brand" href="#">SIGHTLINE<span className="brand-icon" aria-hidden="true"><i/><i/></span></a><p>Never cover the moment.</p><div><span>Built with Video.js v10</span><a href="https://github.com/ngvanhung90/sightline-videojs-v10">Source ↗</a><a href="./LICENSE.txt">Apache 2.0</a><a href="./media/MEDIA-LICENSE.txt">Original media · CC0</a></div></footer>
 </>;
}
createRoot(document.getElementById('root')!).render(<App/>);

