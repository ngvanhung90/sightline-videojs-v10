import { Video } from '@videojs/react/video';
import { SightlinePlayer } from '@/player';
import { VideoSkin } from '@/video/skin';
import type { PlaybackProps } from '../shell/params';
export function Player({ media }: { media?: PlaybackProps }) {
 return <SightlinePlayer><VideoSkin title="The Fold" subtitle="Original SIGHTLINE demo · CC0">
  <Video {...media} src="./media/the-fold.mp4" poster="./media/poster.jpg" playsInline crossOrigin="anonymous">
   <track kind="chapters" src="./media/chapters.vtt" default />
   <track kind="captions" label="English" srcLang="en" src="./media/captions-en.vtt" default />
  </Video>
 </VideoSkin></SightlinePlayer>;
}
