"""Executa duas vezes a CLI e registra a prova de idempotência com hashes."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def hashes(directory):
    return {path.name: "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(directory.iterdir()) if path.is_file()}


def main():
    output = ROOT / "demo/resultado"
    command = [sys.executable, "-X", "utf8", "-B", str(ROOT / "automatizar.py"), "--entrada",
               str(ROOT / "fixtures/pedidos_ficticios.csv"), "--saida", str(output)]
    runs = []
    snapshots = []
    for index in range(2):
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", check=False, timeout=30)
        if result.returncode != 0:
            raise SystemExit("Demonstração recusada: " + result.stdout)
        runs.append({"execucao": index + 1, "exit_code": result.returncode, "resultado": json.loads(result.stdout)})
        snapshots.append(hashes(output))
    proof = {"schema": 1, "dados": "100% fictícios; domínios .example", "execucoes": runs,
             "arquivos_identicos": snapshots[0] == snapshots[1], "primeira": snapshots[0], "segunda": snapshots[1]}
    if not proof["arquivos_identicos"]:
        raise SystemExit("Os resultados mudaram na segunda execução; investigar antes de entregar.")
    (ROOT / "demo/comprovacao.json").write_text(json.dumps(proof, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "execucoes": 2, "arquivos_identicos": True, "pedidos_por_execucao": 4}, ensure_ascii=True))


if __name__ == "__main__":
    main()
