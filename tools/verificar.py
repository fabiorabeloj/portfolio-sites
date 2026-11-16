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
        for key in ("src", "href"):
            if attributes.get(key):
                self.references.append(attributes[key])


def check():
    manifest = json.loads((ROOT / "PROVENIENCIA.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Arquivo inválido no manifesto: " + item["path"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Hash divergente: " + item["path"])
    for name in PAGES:
        parser = Resources()
        parser.feed((ROOT / name).read_text(encoding="utf-8"))
        for reference in parser.references:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc:
                continue  # links públicos não são consultados por este check
            if parsed.path:
                target = (ROOT / unquote(parsed.path)).resolve()
                if not target.is_relative_to(ROOT) or not target.is_file():
                    raise ValueError(f"Recurso local ausente em {name}: {reference}")
            elif parsed.fragment and parsed.fragment not in parser.ids:
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
    return {"pages": len(PAGES), "hashed_files": len(manifest["files"]),
            "package_hashes": package_hashes, "ok": True}


if __name__ == "__main__":
    print(json.dumps(check(), ensure_ascii=False))
