/** Public playback IDs only. No Mux credentials or API calls belong in the skin. */
const muxPlayback = {
  'practice/eight-tap.mp4': 'yKH8XV91pZhQMCxxaVxvHCk1HdOAhZjyIP02jYuwFf01M',
  'practice/eight-tap-portrait.mp4': '7xitq3hbuYjv7HTf00Tz01r1eUrXsZEi3SOD01H136bJN8',
  'handwriting/handwriting.mp4': 'Bi3TzKqTKcWR3aVVCceKxFNrwNeLbiIHr7zJFXwv022w',
} as const;

export function demoMediaUrl(path: string, originControl: boolean) {
  const playback = muxPlayback[path as keyof typeof muxPlayback];
  // The retained origin copy is an explicit HTTP-delivery regression fixture.
  // Other demonstration fixtures continue using their original local assets.
  return playback && !originControl
    ? `https://stream.mux.com/${playback}/highest.mp4`
    : `./media/${path}`;
}
