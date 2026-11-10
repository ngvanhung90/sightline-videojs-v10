"""Original SIGHTLINE demo footage. Source: Apache-2.0; output: CC0-1.0.

Procedural animation, not a player mockup or a recording of player behavior.
No downloads, external images, models, or accounts. Run only inside the owner's
reviewed storage admission, e.g. python -B scripts/generate_media.py --output ...
Requires Pillow, numpy, and imageio-ffmpeg (already available on the host).
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


FPS = 24
LANDSCAPE_DURATION = 32
PALETTE = {
    "table": (69, 87, 82),
    "paper": (239, 228, 207),
    "back": (207, 163, 113),
    "ink": (236, 234, 219),
    "crease": (184, 167, 139),
    "rust": (167, 87, 56),
    "sage": (130, 146, 122),
}


def ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3.0 - 2.0 * x)


def mix(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def font(size: int, serif: bool = False):
    # Rasterized installed fonts only. No font files are copied into the output.
    candidates = (
        ["C:/Windows/Fonts/georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
        if serif else
        ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in candidates:
        if Path(name).is_file():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default(size=size)


class FoldScene:
    def __init__(self, width: int, height: int):
        self.w, self.h = width, height
        self.portrait = height > width
        self.scale = min(width / 960, height / 540)
        self.unit = min(width * (0.67 if self.portrait else 0.33), height * 0.57)
        self.cx = width * (0.50 if self.portrait else 0.60)
        self.cy = height * (0.49 if self.portrait else 0.52)
        rng = np.random.default_rng(3417)
        yy, xx = np.mgrid[:height, :width]
        light = 10 * (1 - xx / width) + 8 * (1 - yy / height)
        light += 6 * np.exp(-((xx / width - .32) ** 2 + (yy / height - .28) ** 2) / .09)
        noise = rng.normal(0, .85, (height, width))
        rgb = np.stack([np.clip(c + light + noise, 0, 255) for c in PALETTE["table"]], axis=2)
        self.background = Image.fromarray(rgb.astype(np.uint8)).convert("RGB")
        # Large, diffuse side light. The studio set is deliberately quiet.
        lighting = Image.new("RGBA", (width, height))
        d = ImageDraw.Draw(lighting)
        d.polygon([(0, 0), (width*.28, 0), (width*.11, height), (0, height)], fill=(231, 222, 196, 10))
        self.background = Image.alpha_composite(self.background.convert("RGBA"), lighting).convert("RGB")
        self.title_font = font(max(18, round(29*self.scale)), serif=True)
        self.small_font = font(max(10, round(11*self.scale)))
        self.number_font = font(max(13, round(14*self.scale)))

    def render(self, t: float, variant: str = "main") -> Image.Image:
        image = self.background.copy()
        if variant == "bright":
            image = Image.blend(image, Image.new("RGB", image.size, (250, 247, 231)), .89)
        elif variant == "dark":
            image = Image.blend(image, Image.new("RGB", image.size, (8, 18, 22)), .82)
        w, h, side = self.w, self.h, self.unit
        half = side / 2
        angle = math.pi * ease((t-16)/7.1)
        outer_x = -half * math.cos(angle)
        lift = half * math.sin(angle)
        # A small realignment becomes a stable, precise fold. It is instructional
        # content: the chapter names refer to this visible geometric action.
        rotation = math.radians(-8 * (1 - ease(t / 11)))
        cs, sn = math.cos(rotation), math.sin(rotation)

        def point(x, y, z=0):
            # Mild oblique view gives the lifted paper a readable height.
            return (self.cx + x*cs-y*sn + z*.12, self.cy + x*sn+y*cs - z*.34)

        def polygon(coords, fill, outline=None, width=1):
            p = [point(*xy) for xy in coords]
            ImageDraw.Draw(image).polygon(p, fill=fill)
            if outline:
                ImageDraw.Draw(image).line(p+[p[0]], fill=outline, width=width, joint="curve")

        # Soft studio shadow underneath the paper, plus fine thickness edge.
        shadow = Image.new("RGBA", image.size)
        sd = ImageDraw.Draw(shadow)
        shadow_left = min(0, outer_x)
        sd.polygon([point(x+side*.025, y+side*.035) for x,y in [(shadow_left,-half),(half,-half),(half,half),(shadow_left,half)]], fill=(10,20,18,95))
        shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, side*.028)))
        image = Image.alpha_composite(image.convert("RGBA"), shadow).convert("RGB")
        polygon([(0,-half),(half,-half),(half,half),(0,half)], PALETTE["paper"], (215,202,176))
        d = ImageDraw.Draw(image)
        # Original geometric print, cut into the two panels so it folds with the
        # paper rather than floating as a UI overlay.
        polygon([(0,-half),(half,-half),(half,-half*.58),(0,-half*.58)], (222,208,181))
        polygon([(half*.52,-half),(half,-half),(half,half),(half*.52,half)], (224,211,187))
        polygon([(half*.59,-half*.30),(half*.83,-half*.30),(half*.83,half*.58),(half*.59,half*.58)], PALETTE["sage"])
        d.line([point(0,-half),point(0,half)], fill=PALETTE["crease"], width=max(1,round(side*.0025)))
        # Alignment guides fade into the scene during chapter 2, representing
        # the edges to bring together rather than decorative player rails.
        guide = ease((t-8)/2) * (1-ease((t-15)/2))
        if guide > .01:
            col = mix(PALETTE["table"], (224,230,209), guide*.8)
            for y in [-half,half]:
                for x in [-half,half]:
                    p=point(x,y)
                    r=max(2,side*.012)
                    d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),outline=col,width=max(1,round(side*.004)))
            d.line([point(-half,-half-side*.07),point(half,-half-side*.07)], fill=col,width=1)

        # Fold shadow travels across the receiving panel.
        if angle > .04 and angle < math.pi-.03:
            foldshadow = Image.new("RGBA", image.size)
            fs = ImageDraw.Draw(foldshadow)
            fs.polygon([point(0,-half),point(max(0,outer_x)+side*.06,-half),point(max(0,outer_x)+side*.06,half),point(0,half)], fill=(35,30,19,round(28+35*math.sin(angle))))
            foldshadow=foldshadow.filter(ImageFilter.GaussianBlur(max(2,side*.025)))
            image=Image.alpha_composite(image.convert("RGBA"),foldshadow).convert("RGB")
        paper_color = mix(PALETTE["paper"], (210,194,163), math.sin(angle)*.25)
        if angle > math.pi/2:
            paper_color = mix(PALETTE["back"], (230,195,147), 1-math.sin(angle))
        polygon([(-0.2,-half),(outer_x,-half,lift),(outer_x,half,lift),(-0.2,half)], paper_color, (202,182,150))
        # A printed ink stripe moves with the original left face while visible.
        if angle < math.pi/2:
            x1=-half*.78*math.cos(angle)
            x2=-half*.54*math.cos(angle)
            z1=half*.78*math.sin(angle)
            z2=half*.54*math.sin(angle)
            polygon([(x1,-half,z1),(x2,-half,z2),(x2,half,z2),(x1,half,z1)], PALETTE["rust"])
        else:
            # Two embossed small marks on the reverse establish a visible
            # front/back transformation without copying any brand mark.
            x=half*.66*(-math.cos(angle))
            z=half*.66*math.sin(angle)
            d=ImageDraw.Draw(image)
            for dy in [-side*.02,side*.02]:
                d.line([point(x-side*.028,side*.3+dy,z),point(x+side*.028,side*.3+dy,z)],fill=(166,124,79),width=max(1,round(side*.004)))
        # Pressing the crease: a highlight passes along the physical hinge.
        if t >= 24:
            d=ImageDraw.Draw(image)
            press=ease((t-24)/5)
            d.line([point(0,-half),point(0,-half+side*press)],fill=(245,225,187),width=max(2,round(side*.008)))

        # Restrained film typography remains above caption-safe picture space.
        d=ImageDraw.Draw(image)
        ink = (47,65,58) if variant == "bright" else PALETTE["ink"]
        left=round(w*.065)
        top=round(h*.085)
        d.text((left,top), "S T U D I O   S I G H T L I N E",font=self.small_font,fill=ink)
        d.text((left,top+round(25*self.scale)), "The Fold",font=self.title_font,fill=ink)
        stages=["Observe","Align the edges","Make the fold","Follow through"]
        stage=min(3,int(t//8))
        y=top+round(73*self.scale)
        d.text((left,y), f"0{stage+1}  /  {stages[stage]}",font=self.small_font,fill=ink)
        if self.portrait:
            d.text((left,round(h*.79)), "A study in motion",font=self.title_font,fill=ink)
        else:
            d.text((left,round(h*.82)), "A study in motion",font=self.small_font,fill=ink)
        return image


def write_video(path: Path, scene: FoldScene, duration: float, *, time_scale=1.0, variant="main", fps=FPS):
    writer=imageio_ffmpeg.write_frames(
        str(path), (scene.w,scene.h), fps=fps, codec="libx264",
        pix_fmt_in="rgb24", pix_fmt_out="yuv420p", quality=7,
        macro_block_size=2, ffmpeg_log_level="error",
        output_params=["-preset","fast","-crf","24","-movflags","+faststart"],
    )
    writer.send(None)
    try:
        for i in range(round(duration*fps)):
            writer.send(np.asarray(scene.render(i/fps*time_scale,variant)))
    finally:
        writer.close()
    print(f"Rendered {path.name}: {duration}s {scene.w}x{scene.h}",flush=True)


def synthesize_audio(path: Path, duration: float):
    """An original sustained ambient tone, not a recording or a composition.

    A quiet fundamental and its harmonics make volume controls audible without
    distracting from instruction. All samples are mathematical synthesis.
    The PCM source is retained alongside the silent video, with no cleanup.
    """
    sample_rate=48000
    t=np.arange(round(duration*sample_rate),dtype=np.float64)/sample_rate
    envelope=np.minimum(1,t/1.7)*np.minimum(1,(duration-t)/2.2)
    # Slow non-periodic-feeling swell; no sequencer, melody, beats, or samples.
    swell=.72+.15*np.sin(2*np.pi*.043*t)+.09*np.sin(2*np.pi*.071*t+.8)
    left=(.105*np.sin(2*np.pi*130.8128*t)+.032*np.sin(2*np.pi*261.6256*t+.2)
          +.017*np.sin(2*np.pi*392.4384*t+.7))*envelope*swell
    right=(.105*np.sin(2*np.pi*130.8128*t)+.032*np.sin(2*np.pi*261.6256*t+.24)
           +.017*np.sin(2*np.pi*392.4384*t+.73))*envelope*swell
    pcm=(np.clip(np.stack([left,right],axis=1),-1,1)*32767).astype("<i2")
    with wave.open(str(path),"wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def mux_audio(silent_path: Path, wav_path: Path, output_path: Path):
    # Preserve both original inputs; refuse to replace an existing destination.
    subprocess.run([
        imageio_ffmpeg.get_ffmpeg_exe(),"-nostdin","-n","-loglevel","error",
        "-i",str(silent_path),"-i",str(wav_path),"-map","0:v:0","-map","1:a:0",
        "-c:v","copy","-c:a","aac","-b:a","128k","-shortest",
        "-movflags","+faststart",str(output_path),
    ],check=True)
    print(f"Muxed original synthesized audio: {output_path.name}",flush=True)


def vtt_time(seconds):
    ms=round(seconds*1000)
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d}.{ms%1000:03d}"


def write_vtt(path: Path, cues):
    text="WEBVTT\n\n"+"\n\n".join(f"{i+1}\n{vtt_time(start)} --> {vtt_time(end)}\n{body}" for i,(start,end,body) in enumerate(cues))+"\n"
    path.write_text(text,encoding="utf-8")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--fps",type=int,default=24,choices=[12,24,30])
    p.add_argument("--width",type=int,default=960,choices=[960,1280])
    args=p.parse_args()
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    # Refuse overwrites: a second run needs a distinct retained-output identity.
    names=["the-fold.mp4","the-fold-silent.mp4","the-fold-ambient.wav","the-fold-portrait.mp4","the-fold-portrait-silent.mp4","the-fold-portrait-ambient.wav","bright.mp4","dark.mp4","short.mp4","poster.jpg","portrait-poster.jpg","chapters.vtt","captions-en.vtt","portrait-chapters.vtt","portrait-captions-en.vtt","MEDIA-LICENSE.txt","media-manifest.json"]
    existing=[name for name in names if (out/name).exists()]
    if existing:
        raise SystemExit("Refusing to overwrite retained output: "+", ".join(existing))
    wide=FoldScene(args.width,args.width*9//16)
    portrait=FoldScene(432,768)
    write_video(out/"the-fold-silent.mp4",wide,32,fps=args.fps)
    synthesize_audio(out/"the-fold-ambient.wav",32)
    mux_audio(out/"the-fold-silent.mp4",out/"the-fold-ambient.wav",out/"the-fold.mp4")
    wide.render(3).save(out/"poster.jpg",quality=94)
    write_video(out/"the-fold-portrait-silent.mp4",portrait,16,time_scale=2,fps=args.fps)
    synthesize_audio(out/"the-fold-portrait-ambient.wav",16)
    mux_audio(out/"the-fold-portrait-silent.mp4",out/"the-fold-portrait-ambient.wav",out/"the-fold-portrait.mp4")
    portrait.render(3).save(out/"portrait-poster.jpg",quality=94)
    write_video(out/"bright.mp4",wide,5,time_scale=4,variant="bright",fps=args.fps)
    write_video(out/"dark.mp4",wide,5,time_scale=4,variant="dark",fps=args.fps)
    write_video(out/"short.mp4",wide,3,time_scale=9,fps=args.fps)
    chapter_titles=["Observe","Align the edges","Make the fold","Follow through"]
    write_vtt(out/"chapters.vtt",[(i*8,(i+1)*8,title) for i,title in enumerate(chapter_titles)])
    captions=[
        (0,4,"Begin with a single sheet. Notice its edges."),
        (4,8,"Give the shape a moment before you move."),
        (8,12,"Square the sheet. Find the centre crease."),
        (12,16,"Align the two outside edges before folding."),
        (16,20,"Lift the left panel toward the centre."),
        (20,24,"Bring it across. Let the edges meet."),
        (24,28,"Press along the crease, from top to bottom."),
        (28,32,"One quiet action. Watch it, then try again."),
    ]
    write_vtt(out/"captions-en.vtt",[(a,b-0.05 if b<32 else b,text) for a,b,text in captions])
    write_vtt(out/"portrait-chapters.vtt",[(i*4,(i+1)*4,title) for i,title in enumerate(chapter_titles)])
    write_vtt(out/"portrait-captions-en.vtt",[(a/2,b/2-0.05 if b<32 else b/2,text) for a,b,text in captions])
    (out/"MEDIA-LICENSE.txt").write_text(
        "SIGHTLINE — The Fold\n\n"
        "Original procedural artwork, animation, chapter text, and caption text created for SIGHTLINE.\n"
        "No external footage, photographs, audio recordings, stock images, or AI models were used.\n"
        "Landscape and portrait audio is original mathematical synthesis: sustained sine harmonics with fades, no song or samples.\n"
        "Generated media and VTT text: CC0 1.0 Universal (public-domain dedication).\n"
        "https://creativecommons.org/publicdomain/zero/1.0/\n"
        "Generator source: Apache License, Version 2.0.\n"
        "Installed system fonts are rasterized into frames; no font files are distributed.\n"
        "The footage demonstrates real motion, not player behavior. Bright/dark/short diagnostic clips are silent.\n"
        "Silent video and PCM WAV intermediates are deliberately retained; no automatic deletion occurs.\n",
        encoding="utf-8",
    )
    manifest={"title":"The Fold — a study in motion","generator":"scripts/generate_media.py","license":"CC0-1.0","audio":{"landscape":True,"portrait":True,"source":"original sustained sine-harmonic synthesis","sample_rate":48000,"channels":2,"encoded_format":"AAC 128kbps","diagnostic_clips":False},"external_assets":[],"retained_intermediates":["the-fold-silent.mp4","the-fold-ambient.wav","the-fold-portrait-silent.mp4","the-fold-portrait-ambient.wav"],"files":[]}
    for name,duration,aspect in [("the-fold.mp4",32,"16:9"),("the-fold-portrait.mp4",16,"9:16"),("bright.mp4",5,"16:9"),("dark.mp4",5,"16:9"),("short.mp4",3,"16:9")]:
        manifest["files"].append({"path":name,"duration_seconds":duration,"aspect_ratio":aspect,"bytes":(out/name).stat().st_size})
    (out/"media-manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
