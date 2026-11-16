"""Confere o MP4 inteiro e produz contato temporal e provas de cortes."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--ffmpeg', default=os.environ.get('FFMPEG_BIN', 'ffmpeg'))
args = parser.parse_args()
FF = Path(shutil.which(args.ffmpeg) or args.ffmpeg).resolve()
PROBE = FF.with_name('ffprobe'+FF.suffix)
assert FF.is_file() and PROBE.is_file(), 'Informe --ffmpeg; ffprobe deve estar ao lado.'
VIDEO = ROOT/'chapa-quente-18s.mp4'
QA = ROOT/'qa'
QA.mkdir(exist_ok=True)


def run(argv, log):
    result = subprocess.run([str(v) for v in argv], check=False, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=120)
    (QA/log).write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, (log, result.returncode)
    return result


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def contact(paths, columns, output, captions):
    cw, ch, bar = 270, 480, 38
    rows = (len(paths)+columns-1)//columns
    canvas = Image.new('RGB', (columns*cw, rows*(ch+bar)), '#141210')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype('C:/Windows/Fonts/seguisb.ttf', 23)
    for i, (path, caption) in enumerate(zip(paths, captions, strict=True)):
        x, y = i % columns*cw, i // columns*(ch+bar)
        with Image.open(path) as source:
            canvas.paste(source.resize((cw, ch)), (x, y))
        draw.text((x+8, y+ch+4), caption, fill='#f4efe8', font=font)
    canvas.save(ROOT/output, quality=94)


meta = json.loads(run([PROBE, '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', VIDEO], 'ffprobe.json').stdout)
v = next(s for s in meta['streams'] if s['codec_type'] == 'video')
a = next(s for s in meta['streams'] if s['codec_type'] == 'audio')
decoded = run([FF, '-hide_banner', '-v', 'error', '-hwaccel', 'none', '-threads', '2', '-i', VIDEO, '-map', '0:v', '-map', '0:a', '-threads', '2', '-f', 'null', '-'], 'decodificacao.log')
black = run([FF, '-hide_banner', '-hwaccel', 'none', '-threads', '2', '-i', VIDEO, '-an', '-filter_threads', '1', '-vf', 'blackdetect=d=0.10:pix_th=0.04:pic_th=0.98', '-f', 'null', '-'], 'quadros-pretos.log')
audio = run([FF, '-hide_banner', '-threads', '1', '-i', VIDEO, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-'], 'audio-loudness.log')
run([FF, '-hide_banner', '-y', '-threads', '2', '-i', VIDEO, '-an', '-filter_threads', '1', '-vf', 'fps=2,scale=270:480', '-q:v', '2', QA/'tempo-%02d.jpg'], 'extracao-temporal.log')
paths = sorted(QA.glob('tempo-*.jpg'))
assert len(paths) == 36
contact(paths, 6, 'contato-quadros.jpg', [f'{i*.5:.1f}–{(i+1)*.5:.1f}s' for i in range(36)])
cut_indices = [71, 72, 179, 180, 287, 288, 395, 396]
selection = 'select=' + '+'.join(f'eq(n\\,{n})' for n in cut_indices) + ',scale=270:480'
run([FF, '-hide_banner', '-y', '-threads', '2', '-i', VIDEO, '-an', '-filter_threads', '1', '-vf', selection, '-fps_mode', 'vfr', '-q:v', '2', QA/'corte-%02d.jpg'], 'extracao-cortes.log')
cuts = sorted(QA.glob('corte-*.jpg'))
assert len(cuts) == 8
contact(cuts, 4, 'contato-cortes.jpg', [f'quadro {n} / {n/30:.3f}s' for n in cut_indices])
for t in (0.7, 3.6, 7.5, 11.2, 16.5):
    run([FF, '-hide_banner', '-y', '-threads', '1', '-ss', str(t), '-i', VIDEO, '-frames:v', '1', '-q:v', '2', QA/f'quadro-{t:.1f}s.jpg'], f'quadro-{t:.1f}s.log')
public_manifest = json.loads((ROOT/'manifesto-publico.json').read_text(encoding='utf-8'))
intact = all(sha(ROOT/item['arquivo']) == item['sha256'] for item in public_manifest['assets'])
internal = ROOT/'fontes-e-direitos.json'
originals = None
if internal.exists():
    provenance = json.loads(internal.read_text(encoding='utf-8'))
    originals = all(sha(item['origem']) == item['sha256'] and Path(item['origem']).stat().st_mtime_ns == item['mtime_ns'] for item in provenance['fontes'])
    assert originals, 'Fonte original alterada'
summary = audio.stderr[audio.stderr.rfind('Summary:'):]
peak = re.search(r'Peak:\s*([-\d.]+) dBFS', summary)
integrated = re.search(r'I:\s*([-\d.]+) LUFS', summary)
checks = {'1080x1920': (v['width'], v['height']) == (1080, 1920), '30fps': v['r_frame_rate'] == '30/1', '540_quadros': int(v['nb_read_frames']) == 540, '18_segundos': abs(float(meta['format']['duration'])-18) < .04, 'h264_yuv420p': v['codec_name'] == 'h264' and v['pix_fmt'] == 'yuv420p', 'aac_estereo_48k': a['codec_name'] == 'aac' and a['channels'] == 2 and a['sample_rate'] == '48000', 'audio_video_alinhados': abs(float(a['duration'])-float(v['duration'])) < .05, 'decodificacao_inteira_sem_erro': not decoded.stderr.strip(), 'sem_quadro_preto_acidental': 'black_start:' not in black.stderr, 'audio_sem_clipping': peak is not None and float(peak.group(1)) < -1, 'audio_nao_silencioso': integrated is not None and float(integrated.group(1)) > -30, 'fontes_intactas': intact, 'contato_cobre18s': len(paths) == 36}
run([FF, '-version'], 'ffmpeg-versao.txt')
run([FF, '-L'], 'ffmpeg-licenca.txt')
report = {'checks': checks, 'video': {'arquivo': VIDEO.name, 'sha256': sha(VIDEO), 'bytes': VIDEO.stat().st_size, 'duracao_s': float(meta['format']['duration'])}, 'audio': {'lufs_i': float(integrated.group(1)) if integrated else None, 'true_peak_dbfs': float(peak.group(1)) if peak else None, 'sumario': summary}, 'revisao_visual': 'Pendente inspeção dos contatos e quadros pelo principal.', 'cortes_s': [2.4, 6, 9.6, 13.2], 'assets_por_hash': intact, 'originais_preservados_nesta_execucao': originals}
(ROOT/'verificacao.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(report, ensure_ascii=False, indent=2))
assert all(checks.values()), 'Verificação falhou; corrigir antes de entregar.'
