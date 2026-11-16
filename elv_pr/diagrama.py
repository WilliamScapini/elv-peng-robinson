"""Continuação em composição para traçar as curvas P–x–y."""
import math
from .eos import montar_sistema, calcular_fase, ErroDeCalculo, LIMITE_FASES_IGUAIS
from .equilibrio import loop_pressao
from .registro import Registro

def chute_wilson(substancias, x, T):
    """Chute inicial de P e y: K_i = (Pc_i/P)·exp[5,373·(1+ω_i)·(1 - Tc_i/T)] (correlação de Wilson)."""
    Psat = [s.Pc * math.exp(5.373 * (1.0 + s.w) * (1.0 - s.Tc / T)) for s in substancias]
    P = sum(xi * ps for xi, ps in zip(x, Psat))
    y = tuple(xi * ps / P for xi, ps in zip(x, Psat))
    return P, y



def bolha_em_T(problema, cfg, k12, T, x, P_inicial, y_inicial):
    """Ponto de bolha a T. Devolve (P, y) ou None se não convergir ou cair na solução trivial."""
    sistema = montar_sistema(problema.substancias, T, problema.R, k12, problema.correlacao_m)
    try:
        bolha = loop_pressao(sistema, x, P_inicial, y_inicial, cfg, Registro(ativo=False), {})
        if not bolha.convergiu:
            return None
        fase_l = calcular_fase(sistema, x, "liquido", bolha.P)
        fase_v = calcular_fase(sistema, bolha.y, "vapor", bolha.P)
    except (ErroDeCalculo, ArithmeticError, ValueError):
        return None
    if fase_v.Z - fase_l.Z < LIMITE_FASES_IGUAIS:
        return None          # as duas fases caíram na mesma raiz (K = 1): não é equilíbrio
    return bolha.P, bolha.y



def calcular_diagrama_pxy(problema, cfg, config, k12, registro, pontos_experimentais):
    """Cada ponto de bolha (x,P,y) também fornece um ponto de orvalho (y,P)."""
    if not config.gerar or config.n_pontos < 2:
        return []
    xs = sorted({i/(config.n_pontos-1) for i in range(config.n_pontos)} |
                {p[0] for p in pontos_experimentais})
    pontos, anterior = [], None
    for x1 in xs:
        x = (x1, 1-x1)
        chutes = [chute_wilson(problema.substancias, x, problema.T)]
        if anterior is not None:
            chutes.insert(0, anterior)
        resultado = None
        for P0, y0 in chutes:
            resultado = bolha_em_T(problema, cfg, k12, problema.T, x, P0, y0)
            if resultado is not None:
                break
        if resultado is None:
            pontos.append(None)
            anterior = None
            registro.adicionar("diagrama_pxy", {"T_K": problema.T, "x1": x1, "convergiu": False})
            continue
        P, y = resultado
        anterior = (P, y)
        ponto = {"T_K": problema.T, "x1": x1, "y1": y[0], "P_atm": P,
                 "k12": k12, "convergiu": True}
        pontos.append(ponto)
        registro.adicionar("diagrama_pxy", ponto)
    return pontos
