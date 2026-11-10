'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useSightline, useSightlineMedia } from '../player';

const MIN_LOOP_SECONDS = 0.25;
const POSITION_EPSILON = 0.001;
const END_EPSILON = 0.02;
const ANNOUNCEMENT_TAIL_MS = 300;
const SEEK_TIMEOUT_MS = 5000;

interface PracticeState {
  pointA: number | null;
  pointB: number | null;
  repeats: number;
  message: string;
}

interface PendingSeek {
  generation: number;
  source: string;
  target: number;
  tolerance: number;
  countRepeat: boolean;
  resumeAfterEnd: boolean;
  intentVersion: number;
  timeout: ReturnType<typeof setTimeout> | null;
}

export interface PracticeLoopOptions {
  sourceKey: string;
  disabled?: boolean;
}

const emptyState = (message = ''): PracticeState => ({
  pointA: null,
  pointB: null,
  repeats: 0,
  message,
});

function practiceTime(seconds: number): string {
  const ticks = Math.max(0, Math.round(seconds * 100));
  const minutes = Math.floor(ticks / 6000);
  const remainder = ((ticks % 6000) / 100).toFixed(2).padStart(5, '0');
  return minutes >= 60
    ? `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, '0')}:${remainder}`
    : `${minutes}:${remainder}`;
}

function hasRange(state: PracticeState): state is PracticeState & {
  pointA: number;
  pointB: number;
} {
  return state.pointA !== null && state.pointB !== null
    && state.pointB - state.pointA >= MIN_LOOP_SECONDS - POSITION_EPSILON;
}

function rangeIsSeekable(video: HTMLVideoElement, start: number, end: number): boolean {
  for (let index = 0; index < video.seekable.length; index += 1) {
    if (video.seekable.start(index) <= start + POSITION_EPSILON
      && video.seekable.end(index) >= end - POSITION_EPSILON) return true;
  }
  return false;
}

/**
 * A–B practice for the native Video.js <Video> media component.
 * Other engines/embeds remain disabled until separately implemented and tested.
 * Canceling a pending operation invalidates its continuation; it does not attempt
 * to undo a native seek that the browser has already started.
 */
export function usePracticeLoop({ sourceKey, disabled = false }: PracticeLoopOptions) {
  const store = useSightline();
  const media = useSightlineMedia();
  const playback = useSightline(state => ({
    currentSrc: state.currentSrc,
    duration: state.duration,
    streamType: state.streamType,
    // Subscribe to loaded/range changes without re-rendering on every time tick.
    canPlay: state.canPlay,
    seekable: state.seekable,
  }));
  const video = typeof HTMLVideoElement !== 'undefined' && media instanceof HTMLVideoElement
    ? media : null;

  const [state, setState] = useState<PracticeState>(() => emptyState());
  const stateRef = useRef(state);
  const mounted = useRef(false);
  const generation = useRef(0);
  const pending = useRef<PendingSeek | null>(null);
  const suppressUntil = useRef(0);
  const frame = useRef<number | null>(null);
  const playingIntent = useRef(false);
  const intentVersion = useRef(0);

  const commit = useCallback((next: PracticeState) => {
    stateRef.current = next;
    if (mounted.current) setState(next);
  }, []);

  const invalidate = useCallback(() => {
    generation.current += 1;
    const operation = pending.current;
    if (operation?.timeout !== null && operation?.timeout !== undefined) clearTimeout(operation.timeout);
    pending.current = null;
    suppressUntil.current = 0;
    if (frame.current !== null) {
      cancelAnimationFrame(frame.current);
      frame.current = null;
    }
  }, []);

  const clear = useCallback((message = '') => {
    invalidate();
    commit(emptyState(message));
  }, [commit, invalidate]);

  const reset = useCallback((announce = true) => {
    clear(announce ? 'Loop stopped. Full video available.' : '');
  }, [clear]);

  const sourceIdentity = useCallback(() => (
    video ? `${sourceKey}\n${video.src}\n${video.currentSrc}` : sourceKey
  ), [sourceKey, video]);

  const isAllowed = useCallback(() => {
    if (disabled || !video || playback.streamType !== 'on-demand'
      || video.readyState < 1 || video.error
      || !Number.isFinite(video.duration) || video.duration < MIN_LOOP_SECONDS) return false;
    for (let index = 0; index < video.seekable.length; index += 1) {
      if (video.seekable.end(index) - video.seekable.start(index)
        >= MIN_LOOP_SECONDS - POSITION_EPSILON) return true;
    }
    return false;
  }, [disabled, playback.streamType, video]);

  const suppressSeekAnnouncement = useCallback(() => (
    pending.current !== null || Date.now() < suppressUntil.current
  ), []);

  const seekToA = useCallback((countRepeat: boolean, resumeAfterEnd: boolean) => {
    const range = stateRef.current;
    if (!video || !isAllowed() || !hasRange(range) || pending.current) return;

    const operation: PendingSeek = {
      generation: generation.current,
      source: sourceIdentity(),
      target: range.pointA,
      tolerance: Math.min(0.1, (range.pointB - range.pointA) / 4),
      countRepeat,
      resumeAfterEnd,
      intentVersion: intentVersion.current,
      timeout: null,
    };
    pending.current = operation;
    suppressUntil.current = 0;

    const isCurrent = () => mounted.current
      && pending.current === operation
      && generation.current === operation.generation
      && sourceIdentity() === operation.source;

    const fail = () => {
      if (isCurrent()) clear('Loop stopped because the return seek could not complete. Set A and B again.');
    };

    operation.timeout = setTimeout(fail, SEEK_TIMEOUT_MS);
    void store.seek(operation.target).then(async actual => {
      if (!isCurrent()) return;
      if (!isAllowed() || video.seeking || !Number.isFinite(actual)
        || Math.abs(actual - operation.target) > operation.tolerance
        || Math.abs(video.currentTime - operation.target) > operation.tolerance) {
        fail();
        return;
      }

      if (operation.timeout !== null) clearTimeout(operation.timeout);
      pending.current = null;
      suppressUntil.current = Date.now() + ANNOUNCEMENT_TAIL_MS;
      if (operation.countRepeat) {
        commit({ ...stateRef.current, repeats: stateRef.current.repeats + 1 });
      }

      // Ended playback pauses natively. Only resume the same operation when no
      // newer observable play/pause intent, reset, or source change intervened.
      if (operation.resumeAfterEnd && playingIntent.current
        && operation.intentVersion === intentVersion.current
        && operation.generation === generation.current
        && sourceIdentity() === operation.source) {
        try {
          await store.play();
        } catch {
          if (mounted.current && operation.generation === generation.current) {
            commit({ ...stateRef.current, message: 'Loop is ready. Press Play to continue.' });
          }
        }
      }
    }).catch(fail);
  }, [clear, commit, isAllowed, sourceIdentity, store, video]);

  useEffect(() => {
    mounted.current = true;
    clear();
    if (!video) return () => { mounted.current = false; invalidate(); };

    playingIntent.current = !video.paused && !video.ended;
    intentVersion.current += 1;

    const validate = () => {
      const range = stateRef.current;
      if (range.pointA === null && range.pointB === null) return;
      if (!isAllowed() || range.pointA === null || range.pointA >= video.duration
        || (range.pointB !== null && (range.pointB > video.duration + POSITION_EPSILON
          || !rangeIsSeekable(video, range.pointA, range.pointB)))) {
        clear('Loop stopped because the available video range changed.');
      }
    };

    const enforce = (endedEvent = false) => {
      const range = stateRef.current;
      if (!hasRange(range) || !isAllowed() || pending.current || video.seeking) return;
      if (video.currentTime < range.pointB) return;
      // Let the native end event finish its pause before returning from B=duration.
      // This avoids confusing that queued pause with a new user pause at A.
      if (range.pointB >= video.duration - END_EPSILON && !endedEvent) return;
      if (video.paused && !video.ended) return;
      seekToA(true, video.ended && playingIntent.current);
    };

    const tick = () => {
      frame.current = null;
      enforce();
      if (hasRange(stateRef.current) && isAllowed() && !video.paused && !video.ended) {
        frame.current = requestAnimationFrame(tick);
      }
    };
    const startFrames = () => {
      if (frame.current === null && hasRange(stateRef.current)
        && !video.paused && !video.ended) frame.current = requestAnimationFrame(tick);
    };

    const onPlay = () => {
      playingIntent.current = true;
      intentVersion.current += 1;
      startFrames();
    };
    const onPause = () => {
      if (!video.ended) {
        playingIntent.current = false;
        intentVersion.current += 1;
      }
      if (frame.current !== null) cancelAnimationFrame(frame.current);
      frame.current = null;
    };
    const onSeeking = () => {
      const operation = pending.current;
      if (operation && sourceIdentity() === operation.source
        && Math.abs(video.currentTime - operation.target) <= operation.tolerance) return;

      // A manual seek must not inherit the automatic seek's announcement tail.
      if (operation) invalidate();
      suppressUntil.current = 0;
      const range = stateRef.current;
      if (hasRange(range) && (video.currentTime < range.pointA - POSITION_EPSILON
        || video.currentTime > range.pointB + POSITION_EPSILON)) {
        clear('Loop stopped after seeking outside the range.');
      }
    };
    const onSeeked = () => { validate(); startFrames(); };
    const onTimeUpdate = () => { validate(); enforce(); startFrames(); };
    const onEnded = () => { validate(); enforce(true); };
    const onSourceReset = () => clear();
    const onError = () => clear('Loop stopped because the video could not load.');

    video.addEventListener('play', onPlay);
    video.addEventListener('pause', onPause);
    video.addEventListener('seeking', onSeeking);
    video.addEventListener('seeked', onSeeked);
    video.addEventListener('timeupdate', onTimeUpdate);
    video.addEventListener('ended', onEnded);
    video.addEventListener('durationchange', validate);
    video.addEventListener('progress', validate);
    video.addEventListener('loadstart', onSourceReset);
    video.addEventListener('emptied', onSourceReset);
    video.addEventListener('error', onError);
    startFrames();

    return () => {
      mounted.current = false;
      invalidate();
      video.removeEventListener('play', onPlay);
      video.removeEventListener('pause', onPause);
      video.removeEventListener('seeking', onSeeking);
      video.removeEventListener('seeked', onSeeked);
      video.removeEventListener('timeupdate', onTimeUpdate);
      video.removeEventListener('ended', onEnded);
      video.removeEventListener('durationchange', validate);
      video.removeEventListener('progress', validate);
      video.removeEventListener('loadstart', onSourceReset);
      video.removeEventListener('emptied', onSourceReset);
      video.removeEventListener('error', onError);
    };
  }, [clear, invalidate, isAllowed, playback.currentSrc, seekToA, sourceIdentity, video]);

  const captureA = useCallback(() => {
    if (!video || !isAllowed()) return;
    const pointA = Math.min(video.currentTime, video.duration - MIN_LOOP_SECONDS);
    if (!rangeIsSeekable(video, pointA, pointA)) return;
    invalidate();
    commit({
      pointA,
      pointB: null,
      repeats: 0,
      message: `Start A set at ${practiceTime(pointA)}. Play forward, then set B.`,
    });
  }, [commit, invalidate, isAllowed, video]);

  const captureB = useCallback(() => {
    const pointA = stateRef.current.pointA;
    if (!video || !isAllowed() || pointA === null) return;
    const pointB = Math.min(video.currentTime, video.duration);
    if (pointB - pointA < MIN_LOOP_SECONDS - POSITION_EPSILON) {
      commit({ ...stateRef.current, message: 'B must be at least 0.25 seconds after A. Play forward and try again.' });
      return;
    }
    if (!rangeIsSeekable(video, pointA, pointB)) {
      commit({ ...stateRef.current, message: 'Choose A and B within the same available video range.' });
      return;
    }
    invalidate();
    commit({
      pointA,
      pointB,
      repeats: 0,
      message: `Loop active: ${practiceTime(pointA)} to ${practiceTime(pointB)}, ${(pointB - pointA).toFixed(2)} seconds.`,
    });
    seekToA(false, false);
  }, [commit, invalidate, isAllowed, seekToA, video]);

  return {
    pointA: state.pointA,
    pointB: state.pointB,
    active: isAllowed() && hasRange(state),
    canLoop: isAllowed(),
    repeats: state.repeats,
    message: state.message,
    captureA,
    captureB,
    reset,
    suppressSeekAnnouncement,
  };
}
