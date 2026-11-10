'use client';
import { BufferingIndicator, CaptionsButton, Container, FullscreenButton, Hotkey, MuteButton, PlayButton, SeekButton, StatusAnnouncer, Time, TimeSlider, VolumeSlider, isMediaSeekCapable } from '@videojs/react';
import { useTranslator } from '@videojs/react/i18n';
import { useEffect, useId, useRef, useState, type ReactNode, type CSSProperties } from 'react';
import { useSightline, useSightlineMedia } from '../player';
import { Icon } from './icons';
import './skin.css';

export interface VideoSkinProps {
  children?: ReactNode; className?: string; style?: CSSProperties;
  title?: string; subtitle?: string; sourceKey?: string;
  initialMode?: 'watch' | 'practice'; practiceDisabled?: boolean;
}
export const formatTime = (time: number) => {
  if (!Number.isFinite(time) || time < 0) return '—:—';
  const n = Math.floor(time);
  return n >= 3600 ? `${Math.floor(n / 3600)}:${String(Math.floor(n / 60) % 60).padStart(2, '0')}:${String(n % 60).padStart(2, '0')}` : `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
};
export function VideoSkin({ children, className = '', style, title = 'The Fold', subtitle = 'A study in motion', sourceKey = '', initialMode = 'watch', practiceDisabled = false }: VideoSkinProps = {}) {
  const t = useTranslator();
  const label = (text: string) => t(`sightline.${text.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`, { default: text });
  const store = useSightline(); const media = useSightlineMedia();
  const state = useSightline(s => ({ currentTime: s.currentTime, duration: s.duration, paused: s.paused, ended: s.ended, playbackRate: s.playbackRate, chapters: s.chaptersCues, streamType: s.streamType, error: s.error }));
  const [mode, setMode] = useState(initialMode); const [chaptersOpen, setChaptersOpen] = useState(true);
  const [pointA, setA] = useState<number | null>(null); const [pointB, setB] = useState<number | null>(null);
  const [message, setMessage] = useState(''); const [loops, setLoops] = useState(0);
  const chapterId = useId();
  const chapterTrigger = useRef<HTMLButtonElement>(null); const internalSeek = useRef(false);
  const looping = pointA !== null && pointB !== null && pointB > pointA;
  const canLoop = !practiceDisabled && state.streamType === 'on-demand' && Number.isFinite(state.duration) && state.duration > 0 && isMediaSeekCapable(media) && Number.isFinite(media.duration) && media.duration > 0;
  const resetLoop = (announce = true) => { setA(null); setB(null); setLoops(0); if (announce) setMessage(label('Loop reset. Full video available.')); };
  useEffect(() => { setA(null); setB(null); setLoops(0); setMessage(''); }, [sourceKey]);
  useEffect(() => {
    if (!(media instanceof HTMLMediaElement)) return;
    const native: HTMLMediaElement = media;
    const reset = () => { setA(null); setB(null); setLoops(0); };
    native.addEventListener('emptied', reset); native.addEventListener('loadstart', reset);
    return () => { native.removeEventListener('emptied', reset); native.removeEventListener('loadstart', reset); };
  }, [media]);
  useEffect(() => { if (!canLoop) { setA(null); setB(null); } }, [canLoop]);
  useEffect(() => {
    if (!looping || !canLoop || !isMediaSeekCapable(media)) return;
    let frame = 0; let disposed = false;
    const native = media instanceof HTMLMediaElement ? media : null;
    let wasPlaying = native ? !native.paused : false;
    const enforce = () => {
      if (disposed || media.seeking || internalSeek.current || media.currentTime < pointB) return;
      const resume = !!native?.ended && wasPlaying;
      internalSeek.current = true;
      void store.seek(pointA).then(async () => {
        internalSeek.current = false;
        if (!disposed) { setLoops(n => n + 1); if (resume) await store.play(); }
      }).catch(() => { internalSeek.current = false; });
    };
    const check = () => { if (!disposed) { enforce(); frame = requestAnimationFrame(check); } };
    const onPlay = () => { wasPlaying = true; };
    const onPause = () => { if (native && !native.ended && native.currentTime < pointB - 0.02) wasPlaying = false; };
    const outside = () => {
      if (!internalSeek.current && (media.currentTime < pointA - 0.15 || media.currentTime > pointB + 0.15)) {
        setA(null); setB(null); setLoops(0); setMessage('Loop reset after seeking outside the range.');
      }
    };
    frame = requestAnimationFrame(check);
    native?.addEventListener('seeking', outside); native?.addEventListener('timeupdate', enforce); native?.addEventListener('ended', enforce); native?.addEventListener('play', onPlay); native?.addEventListener('pause', onPause);
    return () => { disposed = true; cancelAnimationFrame(frame); internalSeek.current = false; native?.removeEventListener('seeking', outside); native?.removeEventListener('timeupdate', enforce); native?.removeEventListener('ended', enforce); native?.removeEventListener('play', onPlay); native?.removeEventListener('pause', onPause); };
  }, [looping, canLoop, media, pointA, pointB, store]);
  const captureA = () => {
    if (!canLoop || !isMediaSeekCapable(media)) return;
    const value = Math.min(media.currentTime, Math.max(0, state.duration - 0.25));
    setA(value); setB(null); setLoops(0); setMessage(`${label('Start A set at')} ${formatTime(value)}. ${label('Play forward, then set B.')}`);
  };
  const captureB = () => {
    if (!canLoop || pointA === null || !isMediaSeekCapable(media)) return;
    const value = Math.min(media.currentTime, state.duration);
    if (value < pointA + 0.25 - 0.001) { setMessage(label('B must be at least 0.25 seconds after A. Play forward and try again.')); return; }
    setB(value); setLoops(0); setMessage(`${label('Loop active')} · ${formatTime(pointA)} – ${formatTime(value)}`);
    internalSeek.current = true; void store.seek(pointA).catch(() => { setMessage(label('Could not seek. Try setting the loop again.')); }).finally(() => { internalSeek.current = false; });
  };
  const activeChapter = state.chapters.findIndex(c => state.currentTime >= c.startTime && state.currentTime < c.endTime);
  return <Container className={`sightline ${className}`} data-theme="sightline" data-preset="video" data-mode={mode} data-loop-active={looping || undefined} style={style} aria-label={`${title} — SIGHTLINE video player`}
    onKeyDown={e => { if (e.key === 'Escape' && chaptersOpen && mode === 'practice') { setChaptersOpen(false); chapterTrigger.current?.focus(); e.stopPropagation(); } }}>
    <div className="sl-screen">
      {children}
      <BufferingIndicator className="sl-loading"><span className="sl-loader" />{label('Loading the moment…')}</BufferingIndicator>
      {state.error && <div className="sl-error" role="alert"><span className="sl-kicker">SIGHTLINE</span><h3>{label('This moment could not load.')}</h3><p>{label('Check your connection or try another source.')}</p><button type="button" onClick={() => { if (media instanceof HTMLMediaElement) media.load(); }}>{label('Try again')}</button></div>}
      {state.ended && !looping && <div className="sl-ended"><span>{label('A moment worth another look.')}</span><PlayButton className="sl-replay"><Icon name="reset" />{label('Watch again')}</PlayButton></div>}
    </div>
    <div className="sl-deck">
      <div className="sl-context">
        <div className="sl-title"><span className="sl-title-mark" aria-hidden="true" /><div><strong>{title}</strong><span>{subtitle}</span></div></div>
        <div className="sl-mode" role="group" aria-label={label('Viewing mode')}>
          <button type="button" aria-pressed={mode === 'watch'} onClick={() => { setMode('watch'); setMessage(label('Watch mode. Playback continues.')); }}>{label('Watch')}</button>
          <button type="button" aria-pressed={mode === 'practice'} onClick={() => { setMode('practice'); setChaptersOpen(true); setMessage(label('Practice mode. Playback continues.')); }}>{label('Practice')}<span aria-hidden="true">↗</span></button>
        </div>
      </div>
      <div className="sl-rails" aria-label={label('Playback and practice rails')}>
        <TimeSlider.Root className="sl-timeline" thumbAlignment="edge" aria-label={label('Seek')}>
          <TimeSlider.Track className="sl-track"><TimeSlider.Buffer className="sl-buffer" /><TimeSlider.Fill className="sl-fill" /></TimeSlider.Track><TimeSlider.Thumb className="sl-thumb" />
          <TimeSlider.Preview className="sl-preview"><TimeSlider.Value type="pointer" /><TimeSlider.ChapterTitle /></TimeSlider.Preview>
        </TimeSlider.Root>
        <div className="sl-guide" aria-hidden="true">
          {state.chapters.map((c, i) => <span className="sl-chapter-tick" key={`${c.startTime}-${i}`} style={{ insetInlineStart: `${c.startTime / state.duration * 100}%` }} />)}
          {pointA !== null && <span className="sl-point sl-point-a" style={{ insetInlineStart: `${pointA / state.duration * 100}%` }}>A</span>}
          {pointB !== null && <span className="sl-point sl-point-b" style={{ insetInlineStart: `${pointB / state.duration * 100}%` }}>B</span>}
          {looping && <span className="sl-loop-range" style={{ insetInlineStart: `${pointA / state.duration * 100}%`, width: `${(pointB - pointA) / state.duration * 100}%` }} />}
        </div>
      </div>
      <div className="sl-transport" role="group" aria-label={label('Playback controls')}>
        <PlayButton className="sl-icon sl-play" render={(props, s) => <button {...props}><Icon name={s.paused ? 'play' : 'pause'} /></button>} />
        <SeekButton className="sl-icon sl-back" seconds={-5} aria-label={label('Back 5 seconds')}><span aria-hidden="true">↶<small>5</small></span></SeekButton>
        <span className="sl-time"><Time.Value type="current" /><span className="sl-time-divider">/</span><Time.Value type="duration" /></span><span className="sl-spacer" />
        <div className="sl-volume"><MuteButton className="sl-icon" render={(props, s) => <button {...props}><Icon name={s.muted ? 'muted' : 'volume'} /></button>} /><VolumeSlider.Root className="sl-volume-slider" aria-label={label('Volume')}><VolumeSlider.Track><VolumeSlider.Fill /></VolumeSlider.Track><VolumeSlider.Thumb /></VolumeSlider.Root></div>
        <CaptionsButton className="sl-icon sl-cc"><Icon name="captions" /><span className="sl-active-dot" /></CaptionsButton>
        <FullscreenButton className="sl-icon" render={(props, s) => <button {...props}><Icon name={s.fullscreen ? 'exit' : 'fullscreen'} /></button>} />
      </div>
      {mode === 'practice' && <div className="sl-practice">
        <div className="sl-practice-top">
          <button type="button" className="sl-chapter-trigger" ref={chapterTrigger} aria-controls={chapterId} aria-expanded={chaptersOpen} onClick={() => setChaptersOpen(v => !v)}><Icon name="chapters" />{label('Chapters')}<span>{state.chapters.length || '—'}</span></button>
          <fieldset className="sl-rates"><legend className="sl-sr">{label('Playback speed')}</legend>{[0.75, 1, 1.25, 1.5, 2].map(rate => <button type="button" key={rate} aria-label={`${rate}× ${label('speed')}`} aria-pressed={state.playbackRate === rate} onClick={() => { store.setPlaybackRate(rate); setMessage(`${label('Playback speed')} ${rate}×`); }}>{rate}×</button>)}</fieldset>
        </div>
        {chaptersOpen && <section className="sl-chapters" id={chapterId} aria-label={label('Video chapters')}>
          <div className="sl-chapter-heading"><span>{label('Find your moment')}</span><button type="button" className="sl-icon" aria-label={label('Close chapters')} onClick={() => { setChaptersOpen(false); chapterTrigger.current?.focus(); }}><Icon name="close" /></button></div>
          {state.chapters.length ? <ol>{state.chapters.map((chapter, i) => <li key={`${chapter.startTime}-${i}`}><button type="button" aria-current={activeChapter === i ? 'true' : undefined} onClick={() => { resetLoop(false); void store.seek(chapter.startTime).catch(() => setMessage(label('Could not seek to this chapter.'))); setMessage(`${label('Chapter starts at')} ${formatTime(chapter.startTime)}`); }}><span className="sl-chapter-index">{String(i + 1).padStart(2, '0')}</span><span className="sl-chapter-copy"><strong>{chapter.text}</strong><span>{formatTime(chapter.startTime)}</span></span><span className="sl-chapter-arrow" aria-hidden="true">↗</span></button></li>)}</ol> : <p className="sl-empty">{label('No chapters in this video. Set your own A–B range below.')}</p>}
        </section>}
        <div className="sl-loop-tools" role="group" aria-label={label('A–B practice loop')}>
          <span className="sl-loop-name"><Icon name="loop" /><span>{label('Repeat a detail')}<small>{looping ? `${label('Loop active')} · ${loops} ${label('repeats')}` : label('A start. B finish. Your pace.')}</small></span></span>
          <div className="sl-loop-buttons"><button type="button" disabled={!canLoop} onClick={captureA}><b>A</b><span>{pointA === null ? label('Set A') : formatTime(pointA)}</span></button><button type="button" disabled={!canLoop || pointA === null} onClick={captureB}><b>B</b><span>{pointB === null ? label('Set B') : formatTime(pointB)}</span></button><button type="button" className="sl-reset" disabled={pointA === null && pointB === null} onClick={() => resetLoop()}><Icon name="reset" /><span>{label('Reset loop')}</span></button></div>
        </div>
        {!canLoop && <p className="sl-loop-note">{label('A–B loop needs a finite, on-demand video. It is unavailable for live or unknown duration.')}</p>}
      </div>}
      <div className="sl-footnote"><span className="sl-wordmark">SIGHTLINE<span aria-hidden="true">〓</span></span><span>{mode === 'watch' ? label('Nothing between you and the moment.') : label('See it. Slow it. Make it yours.')}</span></div>
    </div>
    <p className="sl-sr" role="status" aria-live="polite" aria-atomic="true">{message}</p><StatusAnnouncer className="sl-sr" />
    <Hotkey keys="Space" action="togglePaused" /><Hotkey keys="k" action="togglePaused" /><Hotkey keys="m" action="toggleMuted" /><Hotkey keys="f" action="toggleFullscreen" /><Hotkey keys="c" action="toggleSubtitles" />
    <Hotkey keys="ArrowLeft" action="seekStep" value={-5} /><Hotkey keys="ArrowRight" action="seekStep" value={5} /><Hotkey keys="ArrowUp" action="volumeStep" value={0.05} /><Hotkey keys="ArrowDown" action="volumeStep" value={-0.05} />
  </Container>;
}


