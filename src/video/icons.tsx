import type { SVGProps, ReactNode } from 'react';
export type IconName = 'play' | 'pause' | 'volume' | 'muted' | 'captions' | 'fullscreen' | 'exit' | 'chapters' | 'loop' | 'reset' | 'arrow' | 'close';
/** Original icon set. 24px grid, 1.7px rounded strokes throughout. */
export function Icon({ name, ...props }: SVGProps<SVGSVGElement> & { name: IconName }) {
  const paths: Record<IconName, ReactNode> = {
    play: <path d="m9 5 11 7-11 7Z" />,
    pause: <path d="M8 5v14M16 5v14" />,
    volume: <><path d="M4 9h4l5-4v14l-5-4H4Z" /><path d="M17 8a6 6 0 0 1 0 8M20 5a10 10 0 0 1 0 14" /></>,
    muted: <><path d="M4 9h4l5-4v14l-5-4H4Z" /><path d="m17 9 5 6m0-6-5 6" /></>,
    captions: <><rect x="3" y="5" width="18" height="14" rx="3" /><path d="M10 10a3 3 0 1 0 0 4m7-4a3 3 0 1 0 0 4" /></>,
    fullscreen: <path d="M9 4H4v5m11-5h5v5M4 15v5h5m11-5v5h-5" />,
    exit: <path d="M4 9h5V4m6 0v5h5M9 20v-5H4m11 5v-5h5" />,
    chapters: <><path d="M8 6h12M8 12h12M8 18h12M3 6h1M3 12h1M3 18h1" /></>,
    loop: <><path d="m17 3 4 4-4 4M7 21l-4-4 4-4M21 7H8a5 5 0 0 0-5 5m0 5h13a5 5 0 0 0 5-5" /></>,
    reset: <path d="M4 10a8 8 0 1 1 1 8M4 4v6h6" />,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    close: <path d="m6 6 12 12M18 6 6 18" />,
  };
  return <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
