"""Demonstração pública: CSV de pedidos fictícios -> base limpa e relatório local."""

import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import tempfile
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

FIELDS = ("pedido_id", "cliente", "email", "produto", "quantidade", "valor_unitario", "status")
OUTPUTS = ("pedidos_limpos.csv", "revisar.csv", "duplicatas.csv", "resumo.json", "relatorio.html")
PRODUCER = {"schema": 1, "producer": "demo-publica-csv-fabio"}
MAX_BYTES, MAX_ROWS = 2_000_000, 10_000
STATUS = {"novo": "novo", "em separacao": "em_separacao", "em_separacao": "em_separacao", "enviado": "enviado"}


def normalize_space(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def plain(text):
    return "".join(char for char in unicodedata.normalize("NFD", text.casefold()) if not unicodedata.combining(char))


def normalize(row):
    """Regra da demo; não é validador universal de e-mail, moeda ou ERP."""
    clean = {key: normalize_space(row[key]) for key in FIELDS}
    errors = []
    clean["pedido_id"] = clean["pedido_id"].upper()
    if not re.fullmatch(r"PED-[0-9]{4,12}", clean["pedido_id"]):
        errors.append("pedido_id: use PED- seguido de 4 a 12 dígitos")
    for field in ("cliente", "produto"):
        value = clean[field]
        if not 1 <= len(value) <= 120 or any(unicodedata.category(c) in {"Cc", "Cf"} for c in value):
            errors.append(field + ": texto obrigatório, até 120 caracteres e sem controles ocultos")
    clean["email"] = clean["email"].casefold()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.+\-]{0,63}@[a-z0-9](?:[a-z0-9.\-]{0,188}[a-z0-9])?\.[a-z]{2,24}", clean["email"], re.ASCII):
        errors.append("email: formato não aceito pela demo")
    if not re.fullmatch(r"[0-9]{1,4}", clean["quantidade"]) or not 1 <= int(clean["quantidade"] or "0") <= 9999:
        errors.append("quantidade: inteiro de 1 a 9999")
    else:
        clean["quantidade"] = str(int(clean["quantidade"]))
    money = re.sub(r"^R\$\s*", "", clean["valor_unitario"])
    if not re.fullmatch(r"[0-9]{1,7}(?:[,.][0-9]{1,2})?", money):
        errors.append("valor_unitario: decimal sem separador de milhar, com até 2 casas")
    else:
        amount = Decimal(money.replace(",", "."))
        if not Decimal("0.01") <= amount <= Decimal(1_000_000):
            errors.append("valor_unitario: fora do intervalo da demo")
        else:
            clean["valor_unitario"] = format(amount, ".2f")
    status = STATUS.get(plain(clean["status"]))
    if status is None:
        errors.append("status: use novo, em separação ou enviado")
    else:
        clean["status"] = status
    return clean, errors


def read_inputs(paths):
    records, sources = [], []
    if not 1 <= len(paths) <= 10 or len(set(paths)) != len(paths):
        raise ValueError("Informe de 1 a 10 CSVs distintos.")
    for index, path in enumerate(paths, 1):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
            raise ValueError("Entrada exige CSV regular de até 2 MB.")
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES:
            raise ValueError("Entrada cresceu além do limite.")
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError:
            raise ValueError("CSV deve usar UTF-8; a entrada foi preservada.") from None
        source = "Arquivo " + str(index)
        sources.append({"origem": source, "sha256": hashlib.sha256(raw).hexdigest()})
        try:
            reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", strict=True)
            header = next(reader, None)
            if header != list(FIELDS):
                raise ValueError("Cabeçalho precisa seguir o modelo e usar ponto e vírgula.")
            for cells in reader:
                if not cells:
                    continue
                if len(cells) != len(FIELDS):
                    raise ValueError(f"{source}, linha {reader.line_num}: quantidade de colunas inválida.")
                if len(records) >= MAX_ROWS:
                    raise ValueError("A demo aceita no máximo 10.000 registros no conjunto.")
                raw_row = dict(zip(FIELDS, cells, strict=True))
                clean, errors = normalize(raw_row)
                records.append({"origem": source, "linha": reader.line_num, "original": raw_row,
                                "limpo": clean, "erros": errors})
        except csv.Error:
            raise ValueError("CSV malformado; nenhuma saída foi atualizada.") from None
    return records, sources


def analyze(records, sources):
    groups = defaultdict(list)
    approved, issues, duplicates = [], [], []
    for record in records:
        if record["erros"]:
            issues.append({**record, "motivo": " | ".join(record["erros"]), "tipo": "campo_invalido"})
        groups[record["limpo"]["pedido_id"]].append(record)
    for group in groups.values():
        valid = [record for record in group if not record["erros"]]
        if not valid:
            continue
        signatures = {tuple(record["limpo"][key] for key in FIELDS) for record in valid}
        if len(signatures) > 1 or len(valid) != len(group):
            reason = "Mesmo ID com valores diferentes ou linha inválida; revisar o grupo inteiro"
            issues.extend({**record, "motivo": reason, "tipo": "colisao_id"} for record in valid)
        else:
            approved.append(valid[0]["limpo"])
            duplicates.extend({**record, "motivo": "Repetição idêntica após normalização"} for record in valid[1:])
    approved.sort(key=lambda record: record["pedido_id"])
    issues.sort(key=lambda record: (record["origem"], record["linha"]))
    counts = Counter(record["status"] for record in approved)
    total = sum((Decimal(record["valor_unitario"]) * int(record["quantidade"]) for record in approved), Decimal(0))
    summary = {"schema": 1, "dados": "sinteticos_na_demonstracao", "entradas": sources, "linhas_recebidas": len(records),
        "pedidos_prontos": len(approved), "duplicatas_removidas": len(duplicates), "linhas_para_revisar": len(issues),
        "campos_invalidos_linhas": sum(row["tipo"] == "campo_invalido" for row in issues),
        "colisao_id_linhas": sum(row["tipo"] == "colisao_id" for row in issues),
        "linhas_normalizadas": sum(record["original"] != record["limpo"] for record in records if not record["erros"]),
        "total_pedidos_prontos": format(total, ".2f"), "por_status": dict(sorted(counts.items())),
        "regra": "Snapshot determinístico: sobrescreve somente os resultados próprios; não faz append nem envia pedidos."}
    assert len(records) == len(approved) + len(issues) + len(duplicates)
    return approved, issues, duplicates, summary


def safe_cell(value):
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or any(char in text for char in "\t\r\n"):
        return "'" + text
    return text


def csv_bytes(fields, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: safe_cell(row[key]) for key in fields})
    return stream.getvalue().encode("utf-8-sig")


def table(headers, rows, caption):
    head = "".join('<th scope="col">' + html.escape(label) + "</th>" for label in headers)
    body = "".join("<tr>" + "".join("<td>" + html.escape(str(value)) + "</td>" for value in row) + "</tr>" for row in rows)
    return '<section class="table-scroll" tabindex="0" aria-label="' + html.escape(caption, quote=True) + '"><table><caption>' + html.escape(caption) + "</caption><thead><tr>" + head + "</tr></thead><tbody>" + body + "</tbody></table></section>"


def render_report(records, approved, issues, duplicates, summary):
    labels = ("Pedido", "Cliente", "E-mail", "Produto", "Qtd.", "Valor un.", "Status")
    before = table(labels, ([row["original"][key] for key in FIELDS] for row in records[:100]), "Antes · registros recebidos")
    after = table(labels, ([row[key] for key in FIELDS] for row in approved[:100]), "Depois · pedidos únicos e validados")
    review = table(("Origem", "Linha", "Pedido", "Motivo"), ((row["origem"], row["linha"], row["limpo"]["pedido_id"], row["motivo"]) for row in issues[:100]), "Revisar · nenhuma colisão é resolvida por suposição")
    repeated = table(("Origem", "Linha", "Pedido", "Motivo"), ((row["origem"], row["linha"], row["limpo"]["pedido_id"], row["motivo"]) for row in duplicates[:100]), "Duplicatas · rastreio das repetições removidas")
    received, ready, removed, check = (summary[key] for key in ("linhas_recebidas", "pedidos_prontos", "duplicatas_removidas", "linhas_para_revisar"))
    template = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Pedidos em ordem · demonstração de automação</title><style>
*{box-sizing:border-box} :root{color-scheme:light;--ink:#152b32;--muted:#52646b;--line:#dae2df;--green:#12634f;--paper:#f4f6f1}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'Segoe UI',Arial,sans-serif;line-height:1.5}button,a{font:inherit}
.wrap{max-width:1336px;margin:auto;padding:0 40px}header{border-bottom:1px solid var(--line);background:#fff}.bar{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:80px;flex-wrap:wrap;padding-top:12px;padding-bottom:12px}
.brand{display:flex;align-items:center;gap:12px;font-weight:750}.mark{display:grid;place-items:center;width:38px;height:38px;border-radius:11px;background:var(--ink);color:#fff;font-size:13px}.badge{font-size:12px;font-weight:700;letter-spacing:.05em;color:var(--green);background:#e5f2eb;border-radius:20px;padding:7px 12px}
main{padding:42px 0}.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;font-weight:750;color:var(--green);margin:0 0 10px}h1{font-size:clamp(30px,3.5vw,47px);line-height:1.1;letter-spacing:-.04em;margin:0 0 15px;font-weight:700}h1 span{color:var(--green)}.intro{max-width:680px;color:var(--muted);font-size:16px;margin:0 0 26px}
.hero{display:grid;grid-template-columns:1.7fr 1fr;gap:35px;align-items:center;margin-bottom:28px}.flow{background:var(--ink);color:white;border-radius:18px;padding:22px}.flow small{color:#c0d8cc;font-size:12px}.flow-line{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:14px}.flow strong{font-size:27px}.flow p{margin:0;font-size:12px}.arrow{display:inline-block;width:12px;height:12px;border-top:2px solid #a5d7bf;border-right:2px solid #a5d7bf;transform:rotate(45deg);margin-right:6px}
.brand-subtitle{font-weight:400;color:#52646b}.flow-note{margin-top:16px!important;color:#c0d8cc}.preview-note{margin-top:16px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:26px}.stat{padding:20px 22px;border:1px solid var(--line);border-radius:14px;background:#fff}.stat .number{font-size:34px;line-height:1;font-weight:720;letter-spacing:-.04em}.stat p{font-size:13px;color:var(--muted);margin:8px 0 0}.stat.green{background:#e6f0e8;border-color:#c5dbc9}.stat.amber{background:#fff4e0;border-color:#e8d9b9}
.workspace{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden}.workspace-head{padding:22px 24px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap}h2{font-size:19px;margin:0 0 3px}.hint{margin:0;color:var(--muted);font-size:13px}.tabs{display:flex;flex-wrap:wrap;gap:6px}.tabs button{cursor:pointer;border:1px solid var(--line);background:white;border-radius:8px;padding:8px 12px;color:var(--muted);font-size:13px;font-weight:650}.tabs button[aria-pressed=true]{color:#fff;background:var(--green);border-color:var(--green)}button:focus-visible,a:focus-visible,.table-scroll:focus-visible{outline:3px solid #ac5b16;outline-offset:3px}
.pane{padding:4px 24px 24px}.pane[hidden]{display:none}.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;white-space:nowrap}caption{text-align:left;padding:18px 0 15px;color:var(--muted);font-size:12px}th{text-align:left;padding:12px;background:#f2f5f1;color:#354f56;font-size:11px;text-transform:uppercase;letter-spacing:.04em}td{padding:14px 12px;border-bottom:1px solid #edf0ec}tbody tr:last-child td{border-bottom:0}td:first-child{font-weight:650}a{color:var(--green);text-underline-offset:3px}.downloads{display:flex;flex-wrap:wrap;gap:20px;padding-top:18px;font-size:12px}.footnotes{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:22px;color:var(--muted);font-size:12px}.footnotes strong{color:var(--ink)}.footnotes p{margin:4px 0}footer{padding:22px 0;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
@media(max-width:760px){.wrap{padding-left:20px;padding-right:20px}main{padding-top:28px}.hero{grid-template-columns:1fr;gap:15px}.stats{grid-template-columns:1fr 1fr;gap:10px}.stat{padding:16px}.stat .number{font-size:29px}.workspace-head{padding:18px}.pane{padding-left:18px;padding-right:18px}.footnotes{grid-template-columns:1fr;gap:8px}.badge{font-size:10px}.bar{gap:8px}.brand{font-size:14px}}
</style></head><body><header><div class="wrap bar"><div class="brand"><span class="mark" aria-hidden="true">FR</span> Fabio Rabelo <span class="brand-subtitle">/ Automação</span></div><span class="badge">DEMONSTRAÇÃO · DADOS FICTÍCIOS</span></div></header>
<main><div class="wrap"><div class="hero"><div><p class="eyebrow">De CSV a resultado verificável</p><h1>Pedidos em ordem.<br><span>Sem trabalho repetido.</span></h1><p class="intro">Uma rotina local valida os campos, padroniza os dados e separa o que precisa de revisão. O resultado pode ser conferido linha por linha.</p></div><div class="flow"><small>UM ARQUIVO ENTRA. CADA LINHA TEM DESTINO.</small><div class="flow-line"><div><strong>__RECEIVED__</strong><p>recebidas</p></div><span class="arrow" aria-hidden="true"></span><div><strong>__READY__</strong><p>prontas</p></div><div><strong>__CHECK__</strong><p>para revisar</p></div></div><p class="flow-note">+ __REMOVED__ repetições identificadas e rastreadas</p></div></div>
<section class="stats" aria-label="Resultado do processamento"><div class="stat"><div class="number">__RECEIVED__</div><p>linhas na entrada</p></div><div class="stat green"><div class="number">__READY__</div><p>pedidos únicos prontos</p></div><div class="stat"><div class="number">__REMOVED__</div><p>duplicatas removidas</p></div><div class="stat amber"><div class="number">__CHECK__</div><p>linhas para revisar</p></div></section>
<section class="workspace" aria-labelledby="base-heading"><div class="workspace-head"><div><h2 id="base-heading">Confira a transformação</h2><p class="hint">Mesmos dados. Regras explícitas. Nenhum envio externo.</p></div><nav class="tabs" aria-label="Escolher visão da base"><button type="button" data-view="before" aria-pressed="false" aria-controls="before">Antes</button><button type="button" data-view="after" aria-pressed="true" aria-controls="after">Depois</button><button type="button" data-view="review" aria-pressed="false" aria-controls="review">Revisar</button><button type="button" data-view="duplicates" aria-pressed="false" aria-controls="duplicates">Duplicatas</button></nav></div>
<div class="pane" id="before" hidden>__BEFORE__</div><div class="pane" id="after">__AFTER__<div class="downloads"><a href="pedidos_limpos.csv" download>Baixar CSV limpo</a><a href="resumo.json" download>Conferir resumo JSON</a></div></div><div class="pane" id="review" hidden>__REVIEW__<div class="downloads"><a href="revisar.csv" download>Baixar linhas para revisão</a></div></div><div class="pane" id="duplicates" hidden>__DUPLICATES__<div class="downloads"><a href="duplicatas.csv" download>Baixar rastreio de duplicatas</a></div></div></section>
<div class="footnotes"><div><strong>Colisão de ID não é resolvida por palpite.</strong><p>Todos os registros divergentes ficam para revisão. A base pronta não recebe um valor escolhido arbitrariamente.</p></div><div><strong>Executar de novo não acrescenta cópias.</strong><p>O processo reconstrói o mesmo snapshot. A comparação de hashes entre duas execuções acompanha esta demonstração.</p></div></div><p class="hint preview-note">Prévia limitada às primeiras 100 linhas de cada visão. Os CSVs contêm o resultado completo. E-mails e pedidos são fictícios.</p></div></main>
<footer><div class="wrap">Projeto demonstrativo · Python padrão + HTML local · Sem API, conta ou serviço pago · Nenhum pedido é enviado</div></footer>
<script>document.querySelectorAll('[data-view]').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('[data-view]').forEach(other=>other.setAttribute('aria-pressed',String(other===button)));document.querySelectorAll('.pane').forEach(pane=>{pane.hidden=pane.id!==button.dataset.view;});}));</script></body></html>
"""
    values = {"__RECEIVED__": str(received), "__READY__": str(ready), "__REMOVED__": str(removed), "__CHECK__": str(check),
              "__BEFORE__": before, "__AFTER__": after, "__REVIEW__": review, "__DUPLICATES__": repeated}
    return re.sub(r"__(?:RECEIVED|READY|REMOVED|CHECK|BEFORE|AFTER|REVIEW|DUPLICATES)__", lambda match: values[match.group()], template)


def run(inputs, output):
    inputs = [Path(path).absolute() for path in inputs]
    if any(path.is_symlink() for path in inputs):
        raise ValueError("Não usar entrada simbólica.")
    inputs = [path.resolve() for path in inputs]
    output = Path(output).absolute()
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("Pasta de saída não aceita links simbólicos.")
    if any((output / name).resolve() in inputs for name in (*OUTPUTS, ".demo-csv.json", ".processando.lock")):
        raise ValueError("Entrada e saída colidem; nenhum arquivo foi alterado.")
    records, sources = read_inputs(inputs)
    approved, issues, duplicates, summary = analyze(records, sources)
    exception_fields = ("origem", "linha", *FIELDS, "motivo")
    payloads = {
        "pedidos_limpos.csv": csv_bytes(FIELDS, approved),
        "revisar.csv": csv_bytes(exception_fields, ({"origem": r["origem"], "linha": r["linha"], **r["original"], "motivo": r["motivo"]} for r in issues)),
        "duplicatas.csv": csv_bytes(exception_fields, ({"origem": r["origem"], "linha": r["linha"], **r["original"], "motivo": r["motivo"]} for r in duplicates)),
        "resumo.json": (json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        "relatorio.html": render_report(records, approved, issues, duplicates, summary).encode("utf-8"),
    }
    marker = output / ".demo-csv.json"
    if (output.exists() and any(output.iterdir())
            and (marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 1024
                 or json.loads(marker.read_text(encoding="utf-8")) != PRODUCER)):
        raise ValueError("Pasta não pertence à demo; escolha uma pasta nova para preservar seus arquivos.")
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output / ".processando.lock"
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise ValueError("Pasta em uso ou execução interrompida. Não remover uma trava de processo ativo.") from None
    os.close(descriptor)
    try:
        if any((output / name).is_symlink() for name in (*OUTPUTS, ".demo-csv.json")):
            raise ValueError("Arquivo de saída não aceita link simbólico.")
        marker.write_text(json.dumps(PRODUCER, sort_keys=True) + "\n", encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix=".preparando-", dir=output) as temporary:
            staging = Path(temporary)
            for name, content in payloads.items():
                (staging / name).write_bytes(content)
            for name in OUTPUTS:
                (staging / name).replace(output / name)
    finally:
        lock_path.unlink()
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Demo local de validação e deduplicação de pedidos CSV")
    parser.add_argument("--entrada", nargs="+", required=True, type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        summary = run(args.entrada, args.saida)
    except (ValueError, OSError, csv.Error) as error:
        print(json.dumps({"ok": False, "erro": str(error)}, ensure_ascii=True))
        return 1
    print(json.dumps({"ok": True, "prontos": summary["pedidos_prontos"], "revisar": summary["linhas_para_revisar"],
                      "duplicatas": summary["duplicatas_removidas"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
