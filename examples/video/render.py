"""Motion design de imagens IA existentes. CPU; sem inferência ou rede."""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import time
import wave
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(variable, "1")

# Limites de threads precisam existir antes de importar NumPy.
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL import __version__ as pillow_version

ROOT = Path(__file__).resolve().parent
PROJECT = json.loads((ROOT / "projeto.json").read_text(encoding="utf-8"))
W, H = PROJECT["resolucao"]
FPS = PROJECT["fps"]
DURATION = PROJECT["duracao_s"]
CREAM, ORANGE, DARK = "#f4efe8", "#ff7a1a", "#141210"
FONT_TITLE = Path(os.environ.get("VIDEO_FONT_TITLE", "C:/Windows/Fonts/impact.ttf"))
FONT_BODY = Path(os.environ.get("VIDEO_FONT_BODY", "C:/Windows/Fonts/seguisb.ttf"))
FONTS = {}
TEXT_BOUNDS = []


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ease(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def text_layer(text, size, color=CREAM, body=False):
    key = (text, size, color, body)
    if key not in FONTS:
        font = ImageFont.truetype(str(FONT_BODY if body else FONT_TITLE), size)
        box = font.getbbox(text)
        canvas = Image.new("RGBA", (box[2] - box[0] + 4, box[3] - box[1] + 4))
        ImageDraw.Draw(canvas).text((2 - box[0], 2 - box[1]), text, font=font, fill=color)
        FONTS[key] = canvas
    return FONTS[key]


def label(canvas, text, size, x, y, color=CREAM, body=False, alpha=1, audit=False):
    layer = text_layer(text, size, color, body)
    if alpha < 1:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point(lambda a: round(a * max(0, alpha))))
    if audit:
        bounds = [x, y, x + layer.width, y + layer.height]
        safe = PROJECT["safe_area_texto"]
        assert bounds[0] >= safe[0] and bounds[1] >= safe[1], (text, bounds)
        assert bounds[2] <= safe[2] and bounds[3] <= safe[3], (text, bounds)
        TEXT_BOUNDS.append({"texto": text, "caixa": bounds})
    canvas.paste(layer, (round(x), round(y)), layer)


def soundtrack():
    """Percussão, baixo e plucks matemáticos próprios; sem samples."""
    sr = 48000
    audio = np.zeros((int(sr * DURATION), 2), dtype=np.float64)
    rng = np.random.default_rng(16112026)

    def add(signal, start, gain, pan=0):
        index = round(start * sr)
        count = min(len(signal), len(audio) - index)
        if count <= 0:
            return
        envelope = np.minimum(np.arange(count) / (sr * .003), 1)
        envelope *= np.minimum(np.arange(count)[::-1] / (sr * .008), 1)
        left, right = math.sqrt((1-pan)/2), math.sqrt((1+pan)/2)
        audio[index:index+count, 0] += signal[:count] * envelope * gain * left
        audio[index:index+count, 1] += signal[:count] * envelope * gain * right

    beat = 60 / PROJECT["bpm"]
    for n in range(30):
        start = n * beat
        t = np.arange(int(sr * .32)) / sr
        kick = np.sin(2 * np.pi * (48*t + 52*.035*(1-np.exp(-t/.035)))) * np.exp(-t*17)
        add(kick, start, .6 if n % 4 == 0 else .43)
        if n % 4 in (1, 3):
            t = np.arange(int(sr * .16)) / sr
            noise = rng.normal(0, 1, len(t))
            clap = np.diff(noise, prepend=0) * np.exp(-t*33)
            add(clap, start, .075)
        for offset in (0, .5):
            t = np.arange(int(sr * .07)) / sr
            noise = rng.normal(0, 1, len(t))
            add(np.diff(noise, prepend=0)*np.exp(-t*80), start+offset*beat, .028, (-1)**n*.45)
        bass_note = [38, 38, 41, 36, 38, 45, 41, 36][n % 8]
        freq = 440 * 2**((bass_note-69)/12)
        t = np.arange(int(sr*.42)) / sr
        bass = (np.sin(2*np.pi*freq*t)+.2*np.sin(4*np.pi*freq*t))*np.exp(-t*8)
        add(bass, start+.025, .22)
        if n >= 4 and n % 2 == 0:
            freq = 440 * 2**(([62, 65, 69, 72][(n//2) % 4]-69)/12)
            t = np.arange(int(sr*.7)) / sr
            pluck = (np.sin(2*np.pi*freq*t)+.18*np.sin(4*np.pi*freq*t))*np.exp(-t*8)
            add(pluck, start+.3, .12, .25)
            add(pluck, start+.48, .035, -.4)
    for start in (2.4, 6, 9.6, 13.2):
        t = np.arange(int(sr*.24))/sr
        noise = rng.normal(0, 1, len(t))
        add(np.diff(noise, prepend=0)*np.sin(np.pi*t/.24)**2, start-.12, .035)
    audio *= np.minimum(np.arange(len(audio))/(sr*.02), 1)[:, None]
    audio *= np.minimum(np.arange(len(audio))[::-1]/(sr*.8), 1)[:, None]
    audio *= 10**(-1.5/20) / np.max(np.abs(audio))
    output = ROOT / "audio-original.wav"
    with wave.open(str(output), "wb") as target:
        target.setnchannels(2)
        target.setsampwidth(2)
        target.setframerate(sr)
        target.writeframes((audio*32767).astype("<i2").tobytes())
    return {"sample_rate": sr, "channels": 2, "peak_dbfs": float(20*np.log10(np.max(np.abs(audio)))), "rms_dbfs": float(20*np.log10(np.sqrt(np.mean(audio**2)))), "seed": 16112026, "samples_externos": False}


def photo_window(canvas, photo, rect, phase, direction):
    x1, y1, x2, y2 = rect
    width, height = x2-x1, y2-y1
    zoom = 1.025 + .055*ease(phase)
    scale = max(width/photo.width, height/photo.height)*zoom
    nw, nh = round(photo.width*scale), round(photo.height*scale)
    resized = photo.resize((nw, nh), Image.Resampling.BICUBIC)
    fraction = .5 + direction*.18*(phase-.5)
    left = max(0, min(nw-width, round((nw-width)*fraction)))
    top = max(0, min(nh-height, round((nh-height)*.5)))
    canvas.paste(resized.crop((left, top, left+width, top+height)), (x1, y1))


def frame(index, photos, audit=False):
    t = index/FPS
    number = next(i for i, scene in enumerate(PROJECT["cenas"]) if scene["inicio"] <= t < scene["fim"])
    scene = PROJECT["cenas"][number]
    elapsed = t-scene["inicio"]
    phase = elapsed/(scene["fim"]-scene["inicio"])
    canvas = Image.new("RGB", (W, H), DARK)
    draw = ImageDraw.Draw(canvas)
    if "foto" in scene:
        photo_window(canvas, photos[number], scene["janela"], phase, (-1)**number)
    else:
        # Símbolo vetorial próprio: três traços formam um burger abstrato.
        shift = round(25*(1-ease(elapsed/.6)))
        draw.rounded_rectangle((96, 390+shift, 455, 475+shift), radius=40, fill=ORANGE)
        draw.rounded_rectangle((96, 499+shift, 455, 525+shift), radius=13, fill=CREAM)
        draw.rounded_rectangle((96, 549+shift, 455, 602+shift), radius=25, fill=ORANGE)
        for x in (176, 247, 321):
            draw.line((x, 426+shift, x+18, 413+shift), fill=DARK, width=5)
    draw.rectangle((96, 185, 165 + round(220*ease(phase)), 192), fill=ORANGE)
    label(canvas, "CHAPA QUENTE" if number < 4 else "CONCEITO DE MARCA", 31, 96, 160, body=True, audit=audit)
    y = scene["y"]
    for line_index, line in enumerate(scene["titulo"]):
        entry = ease((elapsed-line_index*.11)/.32)
        color = ORANGE if line_index == 0 or (number == 4 and line_index == 1) else CREAM
        if audit and number == 3:
            assert y+round(32*(1-entry))+text_layer(line, scene["tamanho"], color).height < 1434, 'Título intercepta o aviso'
        label(canvas, line, scene["tamanho"], 96, y+round(32*(1-entry)), color, alpha=.45+.55*entry, audit=audit)
        y += round(scene["tamanho"]*.99)
    if "apoio" in scene:
        label(canvas, scene["apoio"], 43, 96, 1145 if number == 4 else 1360, body=True, audit=audit)
    if "cta" in scene:
        draw.rounded_rectangle((96, 1240, 910, 1352), radius=8, fill=ORANGE)
        label(canvas, scene["cta"], 45, 130, 1272, DARK, body=True, audit=audit)
    # Cartão opaco torna o aviso legível sobre qualquer fotografia.
    draw.rounded_rectangle((80, 1434, 926, 1550), radius=10, fill=DARK)
    label(canvas, PROJECT["aviso"][0], 34, 104, 1450, body=True, audit=audit)
    label(canvas, PROJECT["aviso"][1], 34, 104, 1497, body=True, audit=audit)
    draw.rectangle((96, 1590, 910, 1594), fill="#484039")
    draw.rectangle((96, 1590, 96+round(814*(t/DURATION)), 1594), fill=ORANGE)
    # Marca de corte discreta, sem flash ou vinheta que cubra o produto.
    draw.rectangle((0, 0, max(0, round(18*(1-ease(elapsed/.2)))), H), fill=ORANGE)
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffmpeg", default=os.environ.get("FFMPEG_BIN", "ffmpeg"))
    args = parser.parse_args()
    ffmpeg = Path(shutil.which(args.ffmpeg) or args.ffmpeg).resolve()
    assert ffmpeg.is_file() and FONT_TITLE.is_file() and FONT_BODY.is_file()
    photos = {}
    for number, scene in enumerate(PROJECT["cenas"]):
        if "foto" in scene:
            photos[number] = Image.open(ROOT/"assets"/scene["foto"]).convert("RGB").crop(scene["recorte"])
        for delta in (0, .23, .6):
            sample = round((scene["inicio"]+delta)*FPS)
            frame(sample, photos, audit=True)
    (ROOT/"safe-areas.json").write_text(json.dumps({"limites": PROJECT["safe_area_texto"], "caixas": TEXT_BOUNDS}, ensure_ascii=False, indent=2), encoding="utf-8")
    audio = soundtrack()
    output = ROOT/"chapa-quente-18s.mp4"
    command = [str(ffmpeg), "-hide_banner", "-y", "-threads", "2", "-filter_threads", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-i", str(ROOT/"audio-original.wav"), "-map", "0:v", "-map", "1:a", "-vf", "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,setsar=1", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-threads", "2", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", str(DURATION), str(output)]
    start = time.monotonic()
    with (ROOT/"render.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=log)
        try:
            for index in range(FPS*DURATION):
                process.stdin.write(frame(index, photos).tobytes())
                if index % FPS == 0:
                    print(f"Render {index//FPS}/{DURATION}s", flush=True)
            process.stdin.close()
            code = process.wait(timeout=60)
        except BaseException:
            process.kill()
            process.wait()
            raise
    assert code == 0, 'FFmpeg falhou; consultar render.log'
    frame(round(16.5*FPS), photos).save(ROOT/"capa.png")
    build = {"duracao_render_s": round(time.monotonic()-start, 2), "comando_argv": command, "video_sha256": sha(output), "bytes": output.stat().st_size, "audio": audio, "pillow": pillow_version, "numpy": np.__version__, "fontes_sistema_nao_distribuidas": [str(FONT_TITLE), str(FONT_BODY)], "encoder": "libx264 CPU, 2 threads"}
    (ROOT/"geracao.json").write_text(json.dumps(build, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"saida": str(output), "tempo_s": build["duracao_render_s"], "bytes": build["bytes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
