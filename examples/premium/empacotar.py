"""Empacota o caso estático e registra os hashes de seus arquivos."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = args.saida.resolve()
    if output.exists() or output == root or root in output.parents:
        raise ValueError('Escolha um arquivo novo fora da pasta do caso.')
    files = sorted(p for p in root.rglob('*') if p.is_file()
                   and p.name != 'manifesto.json' and p.suffix not in {'.pyc', '.zip'}
                   and '__pycache__' not in p.parts and not any(part.startswith('.') for part in p.relative_to(root).parts))
    records = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    manifest = root / 'manifesto.json'
    manifest.write_text(json.dumps({'schema': 1, 'caso': 'alto-lume-premium', 'arquivos': records}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted([*files, manifest]):
            name = 'alto-lume-premium/' + path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(json.dumps({'arquivo': output.name, 'arquivos': len(files) + 1, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
