"""Ajuste de um único k12 à isoterma completa por seção áurea."""
import math
from dataclasses import dataclass
from .modelos import preparar_pontos
from .eos import montar_sistema, calcular_fase, ErroDeCalculo, LIMITE_FASES_IGUAIS
from .equilibrio import loop_pressao
from .registro import Registro

RAZAO_AUREA = (math.sqrt(5.0) - 1.0) / 2.0

@dataclass
class AvaliacaoK12:
    k12: float
    P: float
    y: tuple
    dP_pct: float
    dy1_pct: float
    F: float                 # função objetivo (menor = melhor)
    iteracoes_P: int
    convergiu: bool



@dataclass
class Solucao:
    k12: float
    P: float
    y: tuple
    dP_pct: float
    dy1_pct: float
    F: float
    convergiu: bool
    avaliacao_final: int     # número da avaliação de k12 que gerou a solução
    sistema: object
    fase_liquida: object
    fase_vapor: object
    f_liquido: tuple         # fugacidades f_i^L = φ_i^L·x_i·P
    f_vapor: tuple           # fugacidades f_i^V = φ_i^V·y_i·P
    nos_limites: bool        # k12 ótimo colado em uma ponta do intervalo de busca



def erros_experimentais(problema, P, y):
    # Erro de pressão relativo (%) e erro de composição em pontos percentuais.
    # O segundo permanece definido mesmo para y1 experimental igual a zero.
    dP = abs(P - problema.P_exp) / problema.P_exp * 100.0
    dy1 = abs(y[0] - problema.y_exp[0]) * 100.0
    return dP, dy1, dP ** 2 + dy1 ** 2



def avaliar_k12(problema, k12, cfg, registro, avaliacao, etapa, a, b, pontos_experimentais):
    """Ajuste conjunto: média dos erros quadráticos de todos os pontos."""
    pontos = preparar_pontos(problema, pontos_experimentais)
    sistema = montar_sistema(problema.substancias, problema.T, problema.R, k12, problema.correlacao_m)
    resultados = []
    registro_iteracoes = registro if etapa in ("final", "fixo") or registro.detalhado else Registro(ativo=False)
    for indice, ponto in enumerate(pontos, 1):
        try:
            bolha = loop_pressao(sistema, ponto.x, ponto.P_inicial, ponto.y_inicial,
                                 cfg, registro_iteracoes, {"avaliacao_k12": avaliacao, "ponto_experimental": indice})
            if bolha.convergiu:
                fl = calcular_fase(sistema, ponto.x, "liquido", bolha.P)
                fv = calcular_fase(sistema, bolha.y, "vapor", bolha.P)
                if fv.Z - fl.Z < LIMITE_FASES_IGUAIS:
                    bolha = None
        except (ErroDeCalculo, ArithmeticError, ValueError):
            bolha = None
        if bolha is None or not bolha.convergiu:
            av = AvaliacaoK12(k12, float("nan"), (float("nan"),)*2, float("nan"), float("nan"), float("inf"), 0, False)
            break
        dp, dy, f = erros_experimentais(ponto, bolha.P, bolha.y)
        resultados.append((ponto, bolha, dp, dy, f))
    else:
        ponto, bolha, dp, dy, _ = resultados[0]
        av = AvaliacaoK12(k12, bolha.P, bolha.y, dp, dy,
                           sum(r[4] for r in resultados)/len(resultados), bolha.iteracoes, True)
    linha = {"avaliacao": avaliacao, "etapa": etapa, "intervalo_a": a, "intervalo_b": b,
             "k12": k12, "P_calc_atm": av.P, "y1_calc": av.y[0], "y2_calc": av.y[1],
             "dP_pct": av.dP_pct, "dy1_pct": av.dy1_pct, "F": av.F,
             "iteracoes_P": av.iteracoes_P, "convergiu": av.convergiu,
             "desvio_medio_P_pct": sum(r[2] for r in resultados)/len(resultados) if av.convergiu else float("nan"),
             "desvio_medio_y1": sum(r[3] for r in resultados)/len(resultados)/100 if av.convergiu else float("nan")}
    registro.adicionar("loop_k12", linha)
    if etapa in ("final", "fixo") and av.convergiu:
        for i, (ponto, bolha, dp, dy, f) in enumerate(resultados, 1):
            registro.adicionar("pontos_experimentais", {"ponto": i, "x1": ponto.x[0],
                "y1_exp": ponto.y_exp[0], "P_exp_atm": ponto.P_exp, "y1_calc": bolha.y[0],
                "P_calc_atm": bolha.P, "erro_P_pct": dp, "erro_y1_pontos_percentuais": dy, "F_ponto": f})
    return av



def buscar_k12(problema, cfg, ajuste, registro, pontos_experimentais):
    """
    Busca por seção áurea de k12 em [k12_min, k12_max], minimizando
        F = (ΔP%)² + (Δy1%)²
    Não precisa de derivadas e sempre reduz o intervalo em 38,2% por avaliação.
    Devolve (AvaliacaoK12 final, número da avaliação final).
    """
    a, b = ajuste.k12_min, ajuste.k12_max
    c = b - RAZAO_AUREA * (b - a)
    d = a + RAZAO_AUREA * (b - a)

    n = 1
    av_c = avaliar_k12(problema, c, cfg, registro, n, "busca", a, b, pontos_experimentais)
    n = 2
    av_d = avaliar_k12(problema, d, cfg, registro, n, "busca", a, b, pontos_experimentais)

    while (b - a) > cfg.tol_k12 and n < cfg.max_aval_k12 - 1:
        n += 1
        if av_c.F < av_d.F:                  # mínimo em [a, d]
            b, d, av_d = d, c, av_c
            c = b - RAZAO_AUREA * (b - a)
            av_c = avaliar_k12(problema, c, cfg, registro, n, "busca", a, b, pontos_experimentais)
        else:                                # mínimo em [c, b]
            a, c, av_c = c, d, av_d
            d = a + RAZAO_AUREA * (b - a)
            av_d = avaliar_k12(problema, d, cfg, registro, n, "busca", a, b, pontos_experimentais)

    n += 1
    k12_otimo = (a + b) / 2.0
    final = avaliar_k12(problema, k12_otimo, cfg, registro, n, "final", a, b, pontos_experimentais)
    if b - a > cfg.tol_k12:
        final.convergiu = False
        historico = registro.linhas("loop_k12")
        if historico:
            historico[-1]["convergiu"] = False
            historico[-1]["motivo_falha"] = "Limite de avaliações atingido antes de tol_k12."
        registro.limpar("pontos_experimentais")
    return final, n



def resolver(problema, cfg, ajuste, registro, pontos_experimentais):
    """Roda tudo e monta o estado final detalhado (fases, fugacidades) para o relatório."""
    if ajuste.ajustar:
        av, n = buscar_k12(problema, cfg, ajuste, registro, pontos_experimentais)
    else:
        av = avaliar_k12(problema, ajuste.k12_fixo, cfg, registro, 1, "fixo",
                         ajuste.k12_fixo, ajuste.k12_fixo, pontos_experimentais)
        n = 1

    sistema = montar_sistema(problema.substancias, problema.T, problema.R, av.k12, problema.correlacao_m)
    nos_limites = ajuste.ajustar and min(av.k12 - ajuste.k12_min, ajuste.k12_max - av.k12) < 10 * cfg.tol_k12

    if not av.convergiu:
        # sem estado final confiável: o relatório mostra só os loops
        return Solucao(av.k12, av.P, av.y, av.dP_pct, av.dy1_pct, av.F, False, n,
                       sistema, None, None, None, None, nos_limites)

    fase_l = calcular_fase(sistema, problema.x, "liquido", av.P)
    fase_v = calcular_fase(sistema, av.y, "vapor", av.P)
    f_l = tuple(fase_l.phi[i] * problema.x[i] * av.P for i in range(len(problema.x)))
    f_v = tuple(fase_v.phi[i] * av.y[i] * av.P for i in range(len(problema.x)))

    return Solucao(av.k12, av.P, av.y, av.dP_pct, av.dy1_pct, av.F, True, n,
                   sistema, fase_l, fase_v, f_l, f_v, nos_limites)



def calcular_grade_objetivo(problema, cfg, ajuste, registro, pontos_experimentais):
    if not ajuste.ajustar or cfg.n_pontos_grade_f < 3:
        return []
    pontos = []
    for i in range(cfg.n_pontos_grade_f):
        k = ajuste.k12_min + (ajuste.k12_max-ajuste.k12_min)*i/(cfg.n_pontos_grade_f-1)
        av = avaliar_k12(problema, k, cfg, Registro(ativo=False), i+1, "grade", ajuste.k12_min, ajuste.k12_max, pontos_experimentais)
        linha = {"indice": i+1, "k12": k, "F": av.F, "convergiu": av.convergiu}
        registro.adicionar("grade_objetivo", linha)
        pontos.append(linha)
    return pontos
