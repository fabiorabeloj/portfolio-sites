"""Verifica hashes e recursos dos conceitos locais, sem rede ou escrita."""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("index.html", "barbearia.html", "salao.html", "hamburgueria.html")


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []
        self.ids = set()

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        for key in ("src", "href", "poster", "data-ampliar"):
            if attributes.get(key):
                self.references.append(attributes[key])
        for key in ("srcset", "imagesrcset"):
            for source in attributes.get(key, "").split(","):
                if source.strip():
                    self.references.append(source.strip().split()[0])


def check():
    manifest = json.loads((ROOT / "PROVENIENCIA.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Arquivo inválido no manifesto: " + item["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Hash divergente: " + item["path"])
    pages = [ROOT / name for name in PAGES]
    pages.extend(sorted((ROOT / "examples/premium/site").rglob("*.html")))
    report = ROOT / "examples/automation/demo/resultado/relatorio.html"
    if report.is_file():
        pages.append(report)
    documents = {}
    for page in pages:
        parser = Resources()
        parser.feed(page.read_text(encoding="utf-8"))
        documents[page.resolve()] = parser
    references = 0
    for page, parser in documents.items():
        name = page.relative_to(ROOT).as_posix()
        for reference in parser.references:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc:
                continue  # links públicos não são consultados por este check
            references += 1
            target = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
            if target.is_dir():
                target = target / "index.html"
            if not target.is_relative_to(ROOT) or not target.is_file():
                raise ValueError(f"Recurso local ausente em {name}: {reference}")
            if parsed.fragment and target in documents and unquote(parsed.fragment) not in documents[target].ids:
                raise ValueError(f"Âncora ausente em {name}: {reference}")
    package_hashes = 0
    for checksum_file in sorted((ROOT / "examples").glob("*/SHA256SUMS.txt")):
        package = checksum_file.parent.resolve()
        for line in checksum_file.read_text(encoding="utf-8-sig").splitlines():
            digest, relative = line.split(None, 1)
            path = (package / relative.lstrip("*")).resolve()
            if not path.is_relative_to(package) or not path.is_file():
                raise ValueError("Arquivo inválido no pacote: " + relative)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("Hash divergente no pacote: " + relative)
            package_hashes += 1
    premium = ROOT / "examples/premium"
    premium_manifest = premium / "manifesto.json"
    if premium_manifest.is_file():
        for relative, digest in json.loads(premium_manifest.read_text(encoding="utf-8"))["arquivos"].items():
            path = (premium / relative).resolve()
            if not path.is_relative_to(premium) or not path.is_file():
                raise ValueError("Arquivo inválido no premium: " + relative)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("Hash divergente no premium: " + relative)
            package_hashes += 1
    return {"pages": len(pages), "local_references": references,
            "hashed_files": len(manifest["files"]), "package_hashes": package_hashes, "ok": True}


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False))
