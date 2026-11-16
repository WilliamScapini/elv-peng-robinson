"""Regressão contra o artigo e verificações independentes do equilíbrio."""
import math
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from elv_pr.ajuste import resolver, avaliar_k12
from elv_pr.cardano import resolver_cubica
from elv_pr.configuracao import carregar_configuracao
from elv_pr.diagrama import calcular_diagrama_pxy
from elv_pr.eos import calcular_fase, montar_sistema, escolher_raiz, ErroDeCalculo
from elv_pr.registro import Registro

RAIZ = Path(__file__).resolve().parents[1]

# Valores publicados, arredondados como na Tabela 1 do artigo fornecido.
TABELA_ARTIGO = (
    (24.365, .3512, 18.188, .1590),
    (28.818, .4459, 20.057, .2425),
    (30.728, .4793, 21.734, .3090),
    (30.386, .4725, 23.165, .3648),
    (30.056, .4648, 23.919, .3970),
    (30.367, .4778, 25.306, .4704),
    (31.102, .5311, 26.480, .5580),
    (31.419, .5921, 27.209, .6329),
    (31.370, .6751, 27.850, .7208),
    (30.720, .8004, 28.461, .8378),
)


class TestCardano(unittest.TestCase):
    def test_tres_raizes_conhecidas_e_residuos(self):
        resultado = resolver_cubica(-6, 11, -6)
        for raiz, esperada in zip(resultado.raizes, (1, 2, 3)):
            self.assertAlmostEqual(raiz, esperada, places=12)
            self.assertLess(abs(raiz**3 - 6*raiz**2 + 11*raiz - 6), 1e-12)

    def test_raiz_unica_e_repetidas(self):
        unica = resolver_cubica(0, 1, -2)
        self.assertEqual(len(unica.raizes), 1)
        self.assertAlmostEqual(unica.raizes[0], 1, places=12)
        for raiz, esperada in zip(resolver_cubica(0, -3, 2).raizes, (-2, 1, 1)):
            self.assertAlmostEqual(raiz, esperada, places=12)
        for raiz in resolver_cubica(-6, 12, -8).raizes:
            self.assertAlmostEqual(raiz, 2, places=12)

    def test_selecao_de_raiz_fisica(self):
        self.assertEqual(escolher_raiz((.01, .2, .8), .1, "liquido"), .2)
        self.assertEqual(escolher_raiz((.01, .2, .8), .1, "vapor"), .8)
        with self.assertRaises(ErroDeCalculo):
            escolher_raiz((.01, .02), .1, "liquido")


class TestArtigo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = carregar_configuracao(RAIZ / "dados/etanol_agua_200C.json")
        cls.reg_zero, cls.reg_ajuste = Registro(), Registro()
        c = cls.cfg
        cls.zero = resolver(c.problema, c.numerica, replace(c.ajuste, ajustar=False, k12_fixo=0), cls.reg_zero, c.pontos)
        cls.ajustado = resolver(c.problema, c.numerica, c.ajuste, cls.reg_ajuste, c.pontos)

    def test_tabela_1_inteira_nos_algarismos_publicados(self):
        self.assertTrue(self.zero.convergiu and self.ajustado.convergiu)
        zero = self.reg_zero.linhas("pontos_experimentais")
        ajuste = self.reg_ajuste.linhas("pontos_experimentais")
        self.assertEqual(len(zero), 10)
        self.assertEqual(len(ajuste), 10)
        for i, (a, b, esperado) in enumerate(zip(zero, ajuste, TABELA_ARTIGO), 1):
            with self.subTest(ponto=i):
                for real, ref in zip((a["P_calc_atm"], b["P_calc_atm"]), (esperado[0], esperado[2])):
                    self.assertLess(abs(real-ref), .00051)
                for real, ref in zip((a["y1_calc"], b["y1_calc"]), (esperado[1], esperado[3])):
                    self.assertLess(abs(real-ref), .000051)

    def test_minimo_e_desvios_da_tabela_2(self):
        self.assertAlmostEqual(self.ajustado.k12, -.08367651, delta=1e-8)
        self.assertAlmostEqual(self.ajustado.F, 10.08031, delta=1e-5)
        self.assertAlmostEqual(self.zero.F, 933.50884, delta=1e-5)
        self.assertEqual(self.ajustado.avaliacao_final, 42)
        for registro, dp, dy in ((self.reg_zero, 24.141, .09423), (self.reg_ajuste, 2.340, .01670)):
            ultima = registro.linhas("loop_k12")[-1]
            self.assertAlmostEqual(ultima["desvio_medio_P_pct"], dp, delta=.00051)
            self.assertAlmostEqual(ultima["desvio_medio_y1"], dy, delta=.0000051)
        for indice, k, F in ((1, -.11803399, 73.81874), (6, -.08359214, 10.08079), (10, -.08861713, 11.65943)):
            linha = self.reg_ajuste.linhas("loop_k12")[indice-1]
            self.assertAlmostEqual(linha["k12"], k, delta=1e-8)
            self.assertAlmostEqual(linha["F"], F, delta=1e-5)

    def test_igualdade_de_fugacidade_em_todos_os_pontos(self):
        c = self.cfg
        sistema = montar_sistema(c.problema.substancias, c.problema.T, c.problema.R,
                                 self.ajustado.k12, c.problema.correlacao_m)
        for ponto in self.reg_ajuste.linhas("pontos_experimentais"):
            x, y, P = ponto["x1"], ponto["y1_calc"], ponto["P_calc_atm"]
            liquido = calcular_fase(sistema, (x, 1-x), "liquido", P)
            vapor = calcular_fase(sistema, (y, 1-y), "vapor", P)
            self.assertGreater(vapor.Z-liquido.Z, 1e-6)
            for i, (xi, yi) in enumerate(zip((x, 1-x), (y, 1-y))):
                fl, fv = liquido.phi[i]*xi*P, vapor.phi[i]*yi*P
                self.assertLess(abs(math.log(fl/fv)), 1e-10)

    def test_puros_e_continuacao_sem_lacunas(self):
        c = self.cfg
        registro = Registro()
        pontos = calcular_diagrama_pxy(c.problema, c.numerica, c.diagrama,
                                        self.ajustado.k12, registro, c.pontos)
        self.assertTrue(all(p is not None for p in pontos))
        self.assertAlmostEqual(pontos[0]["P_atm"], 15.371, delta=.00051)
        self.assertAlmostEqual(pontos[-1]["P_atm"], 29.022, delta=.00051)
        self.assertEqual(pontos[0]["x1"], pontos[0]["y1"])
        self.assertEqual(pontos[-1]["x1"], pontos[-1]["y1"])
        self.assertTrue(all(p["y1"] > p["x1"] for p in pontos[1:-1]))

    def test_falha_de_um_ponto_invalida_funcao_objetivo(self):
        c = self.cfg
        numerica = replace(c.numerica, max_iter_y=1, max_iter_pressao=1)
        av = avaliar_k12(c.problema, 0, numerica, Registro(), 1, "fixo", 0, 0, c.pontos)
        self.assertFalse(av.convergiu)
        self.assertTrue(math.isinf(av.F))

    def test_limite_de_busca_nao_e_aceito_como_otimo_convergido(self):
        c = self.cfg
        registro = Registro()
        solucao = resolver(c.problema, replace(c.numerica, max_aval_k12=3), c.ajuste, registro, c.pontos)
        self.assertFalse(solucao.convergiu)
        self.assertFalse(registro.linhas("loop_k12")[-1]["convergiu"])
        self.assertEqual(registro.linhas("pontos_experimentais"), [])

    def test_metano_original_e_independencia_entre_entradas(self):
        c = carregar_configuracao(RAIZ / "dados/metano_etano.json")
        registro = Registro()
        solucao = resolver(c.problema, c.numerica, c.ajuste, registro, c.pontos)
        self.assertTrue(solucao.convergiu)
        self.assertTrue(solucao.nos_limites)
        self.assertAlmostEqual(solucao.k12, .09999963159853081, delta=1e-12)
        self.assertAlmostEqual(solucao.F, 3.6369971896689215, delta=1e-9)
        for ponto, P, y in zip(registro.linhas("pontos_experimentais"),
                               (20.58437015272472, 21.682481959840516, 22.505079208302618),
                               (.9852227968461262, .9892490708598629, .992739752876498)):
            self.assertAlmostEqual(ponto["P_calc_atm"], P, delta=1e-9)
            self.assertAlmostEqual(ponto["y1_calc"], y, delta=1e-10)
        # Recalcular o caso anterior não deve utilizar os pontos do metano.
        a = self.cfg
        solucao = resolver(a.problema, a.numerica, a.ajuste, Registro(), a.pontos)
        self.assertAlmostEqual(solucao.k12, self.ajustado.k12, delta=1e-12)


if __name__ == "__main__":
    unittest.main()
