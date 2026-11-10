"""Encode actual Chrome screencast frames at their original per-segment timing.
No synthetic UI or accelerated playback. Portrait captures are letterboxed.
"""
import argparse,json,subprocess
from pathlib import Path
import imageio_ffmpeg
p=argparse.ArgumentParser();p.add_argument('--frames',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.frames.resolve();manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'))
lines=[];total=0.0;count=0
for segment in manifest['segments']:
 frames=segment['frames'];duration=segment['duration_seconds']
 if not frames or duration<=0:raise SystemExit('Missing actual capture frames')
 first=frames[0]['timestamp']
 times=[f['timestamp'] for f in frames]
 if any(b<a for a,b in zip(times,times[1:])) or times[-1]-first>duration+0.25:raise SystemExit('Invalid capture timing')
 total+=duration
 for i,frame in enumerate(frames):
  file=(root/frame['file']).resolve()
  if file.parent!=root or not file.is_file():raise SystemExit('Frame outside capture root')
  start=max(0,frame['timestamp']-first)
  end=frames[i+1]['timestamp']-first if i+1<len(frames) else duration
  delta=min(duration,end)-min(duration,start)
  if delta<=0:continue
  lines.extend(["file '"+file.as_posix().replace("'","'\\''")+"'",f'duration {delta:.6f}'])
  count+=1
 if frames:
  file=(root/frames[-1]['file']).resolve()
# Last frame repeated once so concat honors the previous duration.
lines.append("file '"+file.as_posix().replace("'","'\\''")+"'")
if not 75<=total<=90:raise SystemExit(f'Capture duration outside Owner range: {total}')
a.output.parent.mkdir(parents=True,exist_ok=True)
if a.output.exists():raise SystemExit('Retained recording exists; new lifecycle required')
concat=a.output.with_suffix('.concat.txt');concat.write_text('\n'.join(lines)+'\n',encoding='utf-8')
command=[imageio_ffmpeg.get_ffmpeg_exe(),'-nostdin','-n','-f','concat','-safe','0','-i',str(concat),'-vf','scale=1280:1200:force_original_aspect_ratio=decrease,pad=1280:1200:(ow-iw)/2:(oh-ih)/2:color=0x171c1b,setsar=1','-r','30','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-an','-movflags','+faststart','-t',str(total),str(a.output)]
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
print(result.stdout[-3500:])
if result.returncode:raise SystemExit(result.returncode)
report={'source':manifest.get('source','Actual Chrome viewport capture'),'capture_method':manifest.get('capture_method','Chrome screencast'),'segments':len(manifest['segments']),'frames':count,'duration_seconds':total,'audio':'Silent UI walkthrough','output':str(a.output),'bytes':a.output.stat().st_size}
a.output.with_suffix('.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report))
