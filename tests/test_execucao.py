"""Validação de entradas, linha de comando e rastreabilidade das saídas."""
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from elv_pr import __version__
from elv_pr.cli import main
from elv_pr.configuracao import carregar_configuracao

RAIZ = Path(__file__).resolve().parents[1]


class TestEntrada(unittest.TestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.arquivo = Path(self.pasta.name) / "entrada.json"
        self.dados = json.loads((RAIZ / "dados/etanol_agua_200C.json").read_text())

    def carregar(self):
        self.arquivo.write_text(json.dumps(self.dados, ensure_ascii=False), encoding="utf-8")
        return carregar_configuracao(self.arquivo)

    def test_entradas_invalidas_explicam_o_erro(self):
        original = json.dumps(self.dados)
        casos = (
            (lambda d: d.update(temperatura=10), "desconhecidos"),
            (lambda d: d["condicoes"].update(T_K=True), "número finito"),
            (lambda d: d["substancias"][0].update(Pc_atm=0), "maior que zero"),
            (lambda d: d["pontos_experimentais"][0].update(x1=1.01), "entre 0 e 1"),
            (lambda d: d["pontos_experimentais"][0].update(x1=0), "puros"),
            (lambda d: d["pontos_experimentais"][0].update(P_atm=-1), "maior que zero"),
            (lambda d: d.update(pontos_experimentais=[]), "pelo menos um"),
            (lambda d: d["numerica"].update(max_iter_y=0), "inteiro"),
            (lambda d: d["numerica"].update(n_pontos_grade_f=2), "desativar"),
            (lambda d: d["ajuste_k12"].update(k12_min=.5), "menor que"),
            (lambda d: d["saida"].update(csv_decimal=","), "diferentes"),
            (lambda d: d["diagrama_pxy"].update(gerar="false"), "true ou false"),
        )
        for mutacao, mensagem in casos:
            with self.subTest(erro=mensagem):
                self.dados = json.loads(original)
                mutacao(self.dados)
                with self.assertRaisesRegex(ValueError, mensagem):
                    self.carregar()

    def test_json_repetido_nao_finito_ou_malformado(self):
        for texto in ('{"T":1,"T":2}', '{"T":NaN}', '{"T": 1,}'):
            with self.subTest(json=texto):
                self.arquivo.write_text(texto)
                with self.assertRaises(ValueError):
                    carregar_configuracao(self.arquivo)

    def test_configuracao_minima_tem_padroes(self):
        self.dados = {k: self.dados[k] for k in ("substancias", "condicoes", "pontos_experimentais")}
        cfg = self.carregar()
        self.assertEqual(cfg.numerica.max_iter_y, 200)
        self.assertTrue(cfg.comparar_k12_zero)

    def test_cli_sem_dependencias_a_partir_de_outra_pasta(self):
        self.dados["numerica"]["n_pontos_grade_f"] = 0
        self.dados["diagrama_pxy"]["gerar"] = False
        self.carregar()
        saida = Path(self.pasta.name) / "saída com espaços"
        retorno = subprocess.run([sys.executable, "-S", str(RAIZ/"main.py"), str(self.arquivo),
                                  "--sem-navegador", "--saida", str(saida)],
                                 cwd=self.pasta.name, capture_output=True, text=True, timeout=30)
        self.assertEqual(retorno.returncode, 0, retorno.stderr)
        info = json.loads((saida/"metadados.json").read_text())
        self.assertEqual(info["versao"], __version__)
        self.assertEqual(info["entrada_sha256"], hashlib.sha256(self.arquivo.read_bytes()).hexdigest())
        self.assertEqual((saida/"entrada_utilizada.json").read_bytes(), self.arquivo.read_bytes())
        for nome, esperado in info["saidas_sha256"].items():
            self.assertEqual(hashlib.sha256((saida/nome).read_bytes()).hexdigest(), esperado)
        html = (saida/"relatorio.html").read_text()
        self.assertIn("Etanol + Água", html)
        self.assertNotIn("Metano", html)
        self.assertNotIn("Iterações da pressão", html)
        self.assertIn("Desvio médio", html)
        self.assertTrue((saida/"ajustado/loop_pressao.csv").exists())

    def test_abertura_automatica_e_opcao_sem_navegador(self):
        self.dados["diagrama_pxy"]["gerar"] = False
        self.dados["comparar_k12_zero"] = False
        self.dados["ajuste_k12"]["ajustar"] = False
        self.carregar()
        saida = Path(self.pasta.name) / "saida"
        args = [str(self.arquivo), "--saida", str(saida)]
        with contextlib.redirect_stdout(io.StringIO()), patch("elv_pr.cli.webbrowser.open") as abrir:
            self.assertEqual(main(args), 0)
            abrir.assert_called_once_with((saida/"relatorio.html").as_uri())
            abrir.reset_mock()
            self.assertEqual(main(args + ["--sem-navegador"]), 0)
            abrir.assert_not_called()

    def test_metadados_da_versao_consistentes(self):
        self.assertEqual((RAIZ/"VERSION").read_text().strip(), __version__)
        self.assertIn(f'version: "{__version__}"', (RAIZ/"CITATION.cff").read_text())

    def test_falha_numerica_gera_diagnostico_e_retorna_erro(self):
        self.dados["numerica"].update(max_iter_y=1, max_iter_pressao=1)
        self.dados["comparar_k12_zero"] = False
        self.carregar()
        saida = Path(self.pasta.name) / "falha"
        with contextlib.redirect_stdout(io.StringIO()), patch("elv_pr.cli.webbrowser.open"):
            self.assertEqual(main([str(self.arquivo), "--saida", str(saida), "--sem-navegador"]), 1)
        resumo = json.loads((saida/"resumo.json").read_text())["ajustado"]
        self.assertFalse(resumo["convergiu"])
        self.assertIsNone(resumo["F"])
        self.assertIn("não convergiu", (saida/"relatorio.html").read_text())
        self.assertTrue((saida/"ajustado/loop_k12.csv").exists())

    def test_cli_erro_de_entrada_nao_abre_navegador(self):
        with contextlib.redirect_stderr(io.StringIO()), patch("elv_pr.cli.webbrowser.open") as abrir:
            self.assertEqual(main([str(Path(self.pasta.name)/"inexistente.json")]), 1)
            abrir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
