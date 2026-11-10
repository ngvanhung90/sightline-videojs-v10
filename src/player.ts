import { createPlayer, streamTypeFeature } from '@videojs/react';
import { videoFeatures } from '@videojs/react/video';

/** One provider and media instance for Watch and Practice. */
export const { Player: SightlinePlayer, usePlayer: useSightline, useMedia: useSightlineMedia } = createPlayer({ features: [...videoFeatures, streamTypeFeature] });
