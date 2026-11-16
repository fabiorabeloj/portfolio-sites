import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import automatizar as app

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "fixtures/pedidos_ficticios.csv"


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write_csv(self, rows, name="input.csv"):
        path = self.root / name
        with path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, app.FIELDS, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)
        return path

    @staticmethod
    def row(**changes):
        return {**dict(zip(app.FIELDS, ("PED-9999", "Loja Fictícia", "loja@example.test", "Caneca", "2", "10,50", "novo"), strict=True)), **changes}

    def test_fixture_reconciles_every_row_and_exact_totals(self):
        summary = app.run([FIXTURE], self.root / "result")
        self.assertEqual([summary[key] for key in ("linhas_recebidas", "pedidos_prontos", "duplicatas_removidas", "linhas_para_revisar")], [12, 4, 3, 5])
        self.assertEqual(summary["campos_invalidos_linhas"], 3)
        self.assertEqual(summary["colisao_id_linhas"], 2)
        self.assertEqual(summary["total_pedidos_prontos"], "342.20")
        self.assertEqual(summary["por_status"], {"em_separacao": 1, "enviado": 1, "novo": 2})
        self.assertEqual(len((self.root / "result/pedidos_limpos.csv").read_text(encoding="utf-8-sig").splitlines()), 5)

    def test_second_execution_is_byte_identical_without_append(self):
        destination = self.root / "result"
        app.run([FIXTURE], destination)
        first = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in destination.iterdir()}
        app.run([FIXTURE], destination)
        second = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in destination.iterdir()}
        self.assertEqual(first, second)
        self.assertEqual(len(first), len(app.OUTPUTS) + 1)

    def test_normalization_nfc_spaces_decimal_status_and_email(self):
        row = self.row(cliente="  Cafe\u0301\t Azul  ", email=" LOJA@EXAMPLE.TEST ", quantidade="002", valor_unitario="R$ 10,50", status=" EM SEPARAÇÃO ")
        clean, errors = app.normalize(row)
        self.assertFalse(errors)
        self.assertEqual(clean["cliente"], "Café Azul")
        self.assertEqual(clean["quantidade"], "2")
        self.assertEqual(clean["email"], "loja@example.test")
        self.assertEqual(clean["valor_unitario"], "10.50")
        self.assertEqual(clean["status"], "em_separacao")

    def test_collision_quarantines_whole_group_including_matching_duplicates(self):
        path = self.write_csv([self.row(), self.row(), self.row(quantidade="3")])
        summary = app.run([path], self.root / "result")
        self.assertEqual(summary["pedidos_prontos"], 0)
        self.assertEqual(summary["duplicatas_removidas"], 0)
        self.assertEqual(summary["colisao_id_linhas"], 3)

    def test_invalid_row_with_same_id_prevents_silent_acceptance(self):
        path = self.write_csv([self.row(), self.row(email="invalid")])
        summary = app.run([path], self.root / "result")
        self.assertEqual(summary["pedidos_prontos"], 0)
        self.assertEqual(summary["linhas_para_revisar"], 2)

    def test_multiple_inputs_share_deduplication_and_collision_rules(self):
        first = self.write_csv([self.row()], "one.csv")
        second = self.write_csv([self.row(), self.row(pedido_id="PED-8888")], "two.csv")
        summary = app.run([first, second], self.root / "result")
        self.assertEqual(summary["pedidos_prontos"], 2)
        self.assertEqual(summary["duplicatas_removidas"], 1)
        self.assertEqual(len(summary["entradas"]), 2)

    def test_invalid_structure_encoding_or_quotes_never_updates_outputs(self):
        destination = self.root / "result"
        app.run([FIXTURE], destination)
        before = {name: (destination / name).read_bytes() for name in app.OUTPUTS}
        invalids = [b"wrong;header\n", b"\xff\xfeinvalid", (";".join(app.FIELDS) + '\n"unterminated').encode(),
                    (";".join(app.FIELDS) + "\none;two\n").encode()]
        for index, raw in enumerate(invalids):
            path = self.root / f"invalid-{index}.csv"
            path.write_bytes(raw)
            with self.subTest(index=index), self.assertRaises(ValueError):
                app.run([path], destination)
            self.assertEqual(before, {name: (destination / name).read_bytes() for name in app.OUTPUTS})

    def test_output_cannot_overwrite_input_or_unrelated_files(self):
        path = self.write_csv([self.row()], "pedidos_limpos.csv")
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            app.run([path], self.root)
        self.assertEqual(path.read_bytes(), before)
        destination = self.root / "unrelated"
        destination.mkdir()
        (destination / "notes.txt").write_text("preserve")
        with self.assertRaises(ValueError):
            app.run([FIXTURE], destination)
        self.assertEqual((destination / "notes.txt").read_text(), "preserve")

    def test_existing_run_lock_is_preserved_and_outputs_not_changed(self):
        destination = self.root / "result"
        app.run([FIXTURE], destination)
        lock = destination / ".processando.lock"
        lock.write_text("fixture-active-lock")
        before = (destination / "pedidos_limpos.csv").read_bytes()
        with self.assertRaises(ValueError):
            app.run([FIXTURE], destination)
        self.assertEqual(lock.read_text(), "fixture-active-lock")
        self.assertEqual((destination / "pedidos_limpos.csv").read_bytes(), before)

    def test_html_escapes_data_and_does_not_expand_user_placeholders(self):
        label = '<img src=x onerror="alert(1)"> __AFTER__'
        path = self.write_csv([self.row(cliente=label)])
        app.run([path], self.root / "result")
        report = (self.root / "result/relatorio.html").read_text(encoding="utf-8")
        self.assertNotIn('<img src=x', report)
        self.assertIn("&lt;img", report)
        self.assertIn("__AFTER__", report)

    def test_csv_export_treats_formula_like_text_as_text(self):
        path = self.write_csv([self.row(cliente='=HYPERLINK("https://example.test")')])
        app.run([path], self.root / "result")
        raw = (self.root / "result/pedidos_limpos.csv").read_text(encoding="utf-8-sig")
        row = next(csv.DictReader(io.StringIO(raw), delimiter=";"))
        self.assertTrue(row["cliente"].startswith("'="))

    def test_ambiguous_price_unknown_status_and_bad_quantity_go_to_review(self):
        for key, value in (("valor_unitario", "1.234"), ("valor_unitario", "1e5"), ("quantidade", "2.5"),
                           ("status", "desconhecido"), ("pedido_id", "1001"), ("cliente", "\x00oculto")):
            with self.subTest(key=key, value=value):
                _clean, errors = app.normalize(self.row(**{key: value}))
                self.assertTrue(errors)

    def test_empty_csv_is_valid_and_duplicate_input_path_is_refused(self):
        path = self.write_csv([])
        summary = app.run([path], self.root / "result")
        self.assertEqual(summary["linhas_recebidas"], 0)
        with self.assertRaises(ValueError):
            app.run([path, path], self.root / "other")

    def test_real_cli_success_and_failure_codes(self):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "automatizar.py"), "--entrada", str(FIXTURE), "--saida", str(self.root / "cli")],
                                capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["prontos"], 4)
        result = subprocess.run([sys.executable, "-B", str(ROOT / "automatizar.py"), "--entrada", str(self.root / "missing.csv"), "--saida", str(self.root / "cli")],
                                capture_output=True, text=True, encoding="utf-8", timeout=10, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
