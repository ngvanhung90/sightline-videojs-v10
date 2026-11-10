'use client';

import {
  BufferingIndicator, CaptionsButton, Container, FullscreenButton, Hotkey,
  MuteButton, PlayButton, SeekButton, StatusAnnouncer, Time, TimeSlider, VolumeSlider,
} from '@videojs/react';
import { useTranslator } from '@videojs/react/i18n';
import { useId, useRef, useState, type CSSProperties, type ReactNode } from 'react';
import { useSightline, useSightlineMedia } from '../player';
import { Icon } from './icons';
import { usePracticeLoop } from './use-practice-loop';
import './skin.css';

export interface VideoSkinProps {
  children?: ReactNode;
  className?: string;
  style?: CSSProperties;
  title?: string;
  subtitle?: string;
  sourceKey?: string;
  initialMode?: 'watch' | 'practice';
  practiceDisabled?: boolean;
}

export function formatTime(time: number): string {
  if (!Number.isFinite(time) || time < 0) return '—:—';
  const seconds = Math.floor(time);
  const tail = `${Math.floor(seconds / 60) % 60}:${String(seconds % 60).padStart(2, '0')}`;
  return seconds >= 3600 ? `${Math.floor(seconds / 3600)}:${tail.padStart(5, '0')}` : tail;
}

export function formatPoint(time: number): string {
  if (!Number.isFinite(time) || time < 0) return '—:—';
  const tenths = Math.round(time * 10);
  return `${Math.floor(tenths / 600)}:${String(Math.floor(tenths / 10) % 60).padStart(2, '0')}.${tenths % 10}`;
}

/** Native Video.js Video skin. Mode changes never replace the media element. */
export function VideoSkin({
  children, className = '', style, title = 'Video', subtitle = '', sourceKey = '',
  initialMode = 'watch', practiceDisabled = false,
}: VideoSkinProps = {}) {
  const translate = useTranslator();
  const label = (text: string) => translate(`sightline.${text.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`, { default: text });
  const store = useSightline();
  const media = useSightlineMedia();
  const state = useSightline(s => ({
    currentTime: s.currentTime, duration: s.duration, chapters: s.chaptersCues,
    playbackRate: s.playbackRate, playbackRateAvailability: s.playbackRateAvailability,
    playbackRates: s.playbackRates, streamType: s.streamType, ended: s.ended, error: s.error,
  }));
  const loop = usePracticeLoop({ sourceKey, disabled: practiceDisabled });
  const [mode, setMode] = useState(initialMode);
  const [chaptersOpen, setChaptersOpen] = useState(false);
  const [toolsOpen, setToolsOpen] = useState(false);
  const toolsId = useId();
  const toolsTrigger = useRef<HTMLButtonElement>(null);
  const chapterId = useId();
  const chapterTrigger = useRef<HTMLButtonElement>(null);
  const chapterMessage = useRef(0);
  const [notice, setNotice] = useState('');
  const durationKnown = Number.isFinite(state.duration) && state.duration > 0;
  const activeIndex = state.chapters.reduce((latest, cue, index) => state.currentTime >= cue.startTime ? index : latest, -1);
  const chapter = state.chapters[activeIndex];
  const chapterName = chapter?.text || (state.chapters.length ? label('Choose a chapter') : label('Your own moment'));
  const pointPercent = (time: number) => durationKnown ? Math.max(0, Math.min(100, time / state.duration * 100)) : 0;

  function closeChapters() {
    setChaptersOpen(false);
    chapterTrigger.current?.focus();
  }

  async function selectChapter(index: number) {
    const cue = state.chapters[index];
    if (!cue) return;
    const request = ++chapterMessage.current;
    loop.reset(false);
    setNotice('');
    closeChapters();
    try { await store.seek(cue.startTime); }
    catch { if (request === chapterMessage.current) setNotice(label('Could not seek to this chapter.')); }
  }

  return (
    <Container
      className={`sightline ${className}`} style={style} data-theme="sightline"
      data-preset="video" data-mode={mode} data-loop-active={loop.active || undefined}
      aria-label={`${title} — SIGHTLINE video player`}
      onKeyDown={event => {
        if (event.key === 'Escape' && chaptersOpen) {
          closeChapters();
          event.stopPropagation();
        } else if (event.key === 'Escape' && toolsOpen && mode === 'practice' && toolsTrigger.current?.offsetParent !== null) {
          setToolsOpen(false);
          toolsTrigger.current?.focus();
          event.stopPropagation();
        }
      }}
    >
      <div className="sl-screen">
        {children}
        <BufferingIndicator className="sl-loading"><span className="sl-loader" />{label('Loading the moment…')}</BufferingIndicator>
        {state.error && <div className="sl-error" role="alert">
          <span className="sl-kicker">SIGHTLINE</span>
          <h3>{label('This moment could not load.')}</h3>
          <p>{label('Check your connection or try another source.')}</p>
          {media instanceof HTMLMediaElement && <button type="button" onClick={() => media.load()}>{label('Try again')}</button>}
        </div>}
        {state.ended && !loop.active && <div className="sl-ended">
          <span>{label('A moment worth another look.')}</span>
          <PlayButton className="sl-replay"><Icon name="reset" />{label('Watch again')}</PlayButton>
        </div>}
      </div>

      <div className="sl-deck">
        <div className="sl-context">
          <div className="sl-title"><span className="sl-brand-rails" aria-hidden="true"><i /><i /></span><div><strong>{title}</strong>{subtitle && <span>{subtitle}</span>}</div></div>
          <div className="sl-mode" role="group" aria-label={label('Viewing mode')}>
            <button type="button" aria-pressed={mode === 'watch'} onClick={() => { setMode('watch'); setChaptersOpen(false); setToolsOpen(false); }}>{label('Watch')}</button>
            <button type="button" aria-pressed={mode === 'practice'} onClick={() => setMode('practice')}>{label('Practice')}<span aria-hidden="true">↗</span></button>
          </div>
        </div>

        <div className="sl-rails" role="group" aria-label={label('Dual guide rails')}>
          <div className="sl-rail-heading"><span>{label('Playback')}</span><span className="sl-rail-name">{mode === 'practice' ? label('Find it. Slow it. Repeat it.') : label('The picture stays yours.')}</span></div>
          <TimeSlider.Root className="sl-timeline" thumbAlignment="edge" aria-label={label('Seek')}>
            <TimeSlider.Track className="sl-track"><TimeSlider.Buffer className="sl-buffer" /><TimeSlider.Fill className="sl-fill" /></TimeSlider.Track>
            <TimeSlider.Thumb className="sl-thumb" />
            <TimeSlider.Preview className="sl-preview"><TimeSlider.Value type="pointer" /><TimeSlider.ChapterTitle /></TimeSlider.Preview>
          </TimeSlider.Root>
          <div className="sl-guide" aria-hidden="true">
            <div className="sl-guide-base" />
            {durationKnown && state.chapters.map((cue, index) => <span key={`${cue.startTime}-${index}`} className={`sl-guide-segment ${index === activeIndex ? 'is-current' : ''}`} style={{ insetInlineStart: `${pointPercent(cue.startTime)}%`, width: `${pointPercent(Math.min(cue.endTime, state.duration)) - pointPercent(cue.startTime)}%` }} />)}
            {loop.active && <span className="sl-loop-range" style={{ insetInlineStart: `${pointPercent(loop.pointA!)}%`, width: `${pointPercent(loop.pointB!) - pointPercent(loop.pointA!)}%` }} />}
            {loop.pointA !== null && <span className="sl-point sl-point-a" style={{ insetInlineStart: `${pointPercent(loop.pointA)}%` }}>A</span>}
            {loop.pointB !== null && <span className="sl-point sl-point-b" style={{ insetInlineStart: `${pointPercent(loop.pointB)}%` }}>B</span>}
          </div>
          <div className="sl-guide-meta">
            <button type="button" className="sl-chapter-trigger" ref={chapterTrigger} aria-label={`${label('Chapters')}, ${state.chapters.length}. ${chapterName}`} aria-controls={chapterId} aria-expanded={chaptersOpen} onClick={() => setChaptersOpen(open => !open)}>
              <span className="sl-step-number">{chapter ? String(activeIndex + 1).padStart(2, '0') : '—'}</span>
              <span className="sl-step-copy"><span>{state.chapters.length ? `${label('Chapter')} ${activeIndex >= 0 ? activeIndex + 1 : '—'} / ${state.chapters.length}` : label('Guide rail')}</span><strong>{chapterName}</strong></span>
              <Icon name="chapters" /><span className="sl-open-word">{label('Chapters')}</span>
            </button>
            {loop.active ? <div className="sl-loop-summary"><span><b>{formatPoint(loop.pointA!)}–{formatPoint(loop.pointB!)}</b><small>{(loop.pointB! - loop.pointA!).toFixed(1)}s · {loop.repeats} {label('repeats')}</small></span><button type="button" onClick={() => { loop.reset(); chapterTrigger.current?.focus(); }}>{label('Stop loop')}</button></div>
              : <span className="sl-guide-hint">{mode === 'practice' ? label('Your practice range lives here.') : label('Guide rail')}</span>}
          </div>
        </div>

        {chaptersOpen && <section className="sl-chapters" id={chapterId} aria-label={label('Video chapters')}>
          <div className="sl-chapter-heading"><span>{label('Go straight to the detail')}</span><button type="button" className="sl-icon" aria-label={label('Close chapters')} onClick={closeChapters}><Icon name="close" /></button></div>
          {state.chapters.length ? <ol>{state.chapters.map((cue, index) => <li key={`${cue.startTime}-${index}`}><button type="button" aria-current={index === activeIndex ? 'true' : undefined} onClick={() => { void selectChapter(index); }}><span className="sl-chapter-index">{String(index + 1).padStart(2, '0')}</span><strong>{cue.text}</strong><span className="sl-chapter-time">{formatTime(cue.startTime)}</span></button></li>)}</ol>
            : <p className="sl-empty">{label('No chapters supplied. In Practice, set A and B to make your own range.')}</p>}
        </section>}

        <div className="sl-transport" role="group" aria-label={label('Playback controls')}>
          <PlayButton className="sl-icon sl-play" render={(props, state) => <button {...props}><Icon name={state.paused ? 'play' : 'pause'} /></button>} />
          <SeekButton className="sl-icon sl-back" seconds={-5} aria-label={label('Back 5 seconds')}><span aria-hidden="true">↶<small>5</small></span></SeekButton>
          <span className="sl-time"><Time.Value type="current" /><span className="sl-time-divider">/</span>{state.streamType === 'live' ? <span>{label('Live')}</span> : <Time.Value type="duration" />}</span>
          <span className="sl-spacer" />
          <div className="sl-volume"><MuteButton className="sl-icon" render={(props, state) => <button {...props}><Icon name={state.muted ? 'muted' : 'volume'} /></button>} /><VolumeSlider.Root className="sl-volume-slider" aria-label={label('Volume')}><VolumeSlider.Track className="sl-volume-track"><VolumeSlider.Fill className="sl-volume-fill" /></VolumeSlider.Track><VolumeSlider.Thumb className="sl-volume-thumb" /></VolumeSlider.Root></div>
          <CaptionsButton className="sl-icon sl-cc"><Icon name="captions" /><span className="sl-active-dot" /></CaptionsButton>
          <FullscreenButton className="sl-icon" render={(props, state) => <button {...props}><Icon name={state.fullscreen ? 'exit' : 'fullscreen'} /></button>} />
        </div>

        {mode === 'practice' && <div className="sl-practice" data-tools-open={toolsOpen || undefined}>
          <div className="sl-practice-label"><span className="sl-kicker">{label('Practice')}</span><span>{label('One detail. Your pace.')}</span></div>
          <button className="sl-tools-trigger" ref={toolsTrigger} type="button" aria-expanded={toolsOpen} aria-controls={toolsId} onClick={() => setToolsOpen(open => !open)}><Icon name="loop" /><span>{label('Speed & loop')}</span><b>{state.playbackRate}×</b><span aria-hidden="true">{toolsOpen ? '−' : '+'}</span></button>
          <div className="sl-practice-actions" id={toolsId}>
          <fieldset className="sl-rates"><legend className="sl-sr">{label('Playback speed')}</legend>{[0.75, 1, 1.25, 1.5, 2].map(rate => <button type="button" key={rate} disabled={state.playbackRateAvailability !== 'available' || !state.playbackRates.includes(rate)} aria-label={`${rate}× ${label('speed')}`} aria-pressed={state.playbackRate === rate} onClick={() => store.setPlaybackRate(rate)}>{rate}×</button>)}</fieldset>
          <div className="sl-loop-buttons" role="group" aria-label={label('A–B practice loop')}>
            <button type="button" disabled={!loop.canLoop} aria-label={`${label('Set loop start A')}${loop.pointA !== null ? `, ${formatPoint(loop.pointA)}` : ''}`} onClick={loop.captureA}><b>A</b><span>{loop.pointA === null ? label('Set start') : formatPoint(loop.pointA)}</span></button>
            <button type="button" disabled={!loop.canLoop || loop.pointA === null} aria-label={`${label('Set loop end B')}${loop.pointB !== null ? `, ${formatPoint(loop.pointB)}` : ''}`} onClick={loop.captureB}><b>B</b><span>{loop.pointB === null ? label('Set end') : formatPoint(loop.pointB)}</span></button>
            <button type="button" className="sl-reset" aria-label={label('Reset loop')} disabled={loop.pointA === null && loop.pointB === null} onClick={() => { loop.reset(); chapterTrigger.current?.focus(); }}><Icon name="reset" /><span>{label('Reset')}</span></button>
          </div>
          {!loop.canLoop && <p className="sl-loop-note">{label('A–B needs a finite, on-demand native video at least 0.25 seconds long.')}</p>}
          </div>
        </div>}
        <div className="sl-footnote"><span>SIGHTLINE<span className="sl-tiny-rails" aria-hidden="true">〓</span></span><span>{mode === 'watch' ? label('Never cover the moment.') : label('Watch once. Make it yours.')}</span></div>
      </div>
      <p className="sl-sr" role="status" aria-live="polite" aria-atomic="true">{loop.message || notice}</p>
      <StatusAnnouncer className="sl-sr" labels={{ seekedTo: time => loop.suppressSeekAnnouncement() ? '' : `${label('Seeked to')} ${formatPoint(time)}` }} />
      <Hotkey keys="Space" action="togglePaused" /><Hotkey keys="k" action="togglePaused" />
      <Hotkey keys="m" action="toggleMuted" /><Hotkey keys="f" action="toggleFullscreen" /><Hotkey keys="c" action="toggleSubtitles" />
      <Hotkey keys="ArrowLeft" action="seekStep" value={-5} /><Hotkey keys="ArrowRight" action="seekStep" value={5} />
      <Hotkey keys="ArrowUp" action="volumeStep" value={0.05} /><Hotkey keys="ArrowDown" action="volumeStep" value={-0.05} />
    </Container>
  );
}
