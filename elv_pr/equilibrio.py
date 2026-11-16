"""Iterações aninhadas de pressão e composição do vapor (abordagem φ–φ)."""
from dataclasses import dataclass
from .eos import calcular_fase

@dataclass
class ResultadoY:
    y: tuple
    S: float                 # Σ K_i·x_i no ponto convergido
    K: tuple
    fase_vapor: object
    iteracoes: int
    convergiu: bool



@dataclass
class ResultadoBolha:
    P: float
    y: tuple
    S: float
    iteracoes: int
    convergiu: bool



def _por_componente(prefixo, valores, sufixo=""):
    """('phi', (0.9, 0.1), '_L') -> {'phi1_L': 0.9, 'phi2_L': 0.1}"""
    return {"%s%d%s" % (prefixo, i + 1, sufixo): v for i, v in enumerate(valores)}



def calcular_fase_registrando(sistema, z, fase, P, registro, contexto):
    """calcular_fase() + uma linha em 'raizes_cardano' com tudo que o Cardano calculou."""
    res = calcular_fase(sistema, z, fase, P)
    c = res.cardano
    raizes = list(c.raizes) + [""] * (3 - len(c.raizes))
    linha = dict(contexto)
    linha.update({"fase": fase, "P_atm": P})
    linha.update(_por_componente("z", res.z))
    linha.update({
        "A": res.A, "B": res.B,
        "coef1": 1.0, "coef2": c.a2, "coef3": c.a1, "coef4": c.a0,
        "p": c.p, "q": c.q, "discriminante": c.discriminante, "caso": c.caso,
        "raiz_1": raizes[0], "raiz_2": raizes[1], "raiz_3": raizes[2],
        "Z_escolhido": res.Z,
    })
    registro.adicionar("raizes_cardano", linha)
    return res



def loop_y(sistema, fase_liquida, P, y_inicial, cfg, registro, contexto):
    """
    Substituição sucessiva:  y -> φ^V(y) -> K = φ^L/φ^V -> y_novo = K·x / Σ K·x
    Repete até a variação máxima de y ficar menor que cfg.tol_y.
    """
    x = fase_liquida.z
    n = len(x)
    y = tuple(y_inicial)

    for it in range(1, cfg.max_iter_y + 1):
        ctx = dict(contexto)
        ctx["iter_y"] = it
        fase_v = calcular_fase_registrando(sistema, y, "vapor", P, registro, ctx)

        K = tuple(fase_liquida.phi[i] / fase_v.phi[i] for i in range(n))
        y_nao_norm = tuple(K[i] * x[i] for i in range(n))
        S = sum(y_nao_norm)
        y_novo = tuple(v / S for v in y_nao_norm)
        erro = max(abs(y_novo[i] - y[i]) for i in range(n))

        linha = dict(ctx)
        linha["P_atm"] = P
        linha.update(_por_componente("y", y, "_entrada"))
        linha.update({"A_V": fase_v.A, "B_V": fase_v.B, "Z_V": fase_v.Z})
        linha.update(_por_componente("phi", fase_v.phi, "_V"))
        linha.update(_por_componente("phi", fase_liquida.phi, "_L"))
        linha.update(_por_componente("K", K))
        linha.update(_por_componente("Kx", y_nao_norm))
        linha["S"] = S
        linha.update(_por_componente("y", y_novo, "_novo"))
        linha["erro_max_y"] = erro
        registro.adicionar("loop_y", linha)

        y = y_novo
        if erro < cfg.tol_y:
            return ResultadoY(y, S, K, fase_v, it, True)

    return ResultadoY(y, S, K, fase_v, cfg.max_iter_y, False)



def loop_pressao(sistema, x, P_inicial, y_inicial, cfg, registro, contexto):
    """
    Para cada P: resolve o loop de y e calcula S = Σ K_i·x_i.
    No equilíbrio S = 1. Como K ∝ 1/P aproximadamente, atualiza P_novo = P·S.
    """
    P = P_inicial
    y = tuple(y_inicial)

    for it in range(1, cfg.max_iter_pressao + 1):
        ctx = dict(contexto)
        ctx["iter_P"] = it
        ctx["iter_y"] = ""

        fase_l = calcular_fase_registrando(sistema, x, "liquido", P, registro, ctx)
        res_y = loop_y(sistema, fase_l, P, y, cfg, registro, ctx)

        S = res_y.S
        erro = abs(S - 1.0)
        P_novo = P * S

        linha = dict(ctx)
        linha["P_atm"] = P
        linha.update({"A_L": fase_l.A, "B_L": fase_l.B, "Z_L": fase_l.Z, "Z_V": res_y.fase_vapor.Z})
        linha.update(_por_componente("phi", fase_l.phi, "_L"))
        linha.update(_por_componente("phi", res_y.fase_vapor.phi, "_V"))
        linha["iteracoes_y"] = res_y.iteracoes
        linha.update(_por_componente("y", res_y.y))
        linha.update(_por_componente("K", res_y.K))
        linha["S"] = S
        linha["erro_S_menos_1"] = erro
        linha["P_novo_atm"] = P_novo
        registro.adicionar("loop_pressao", linha)

        y = res_y.y
        if erro < cfg.tol_pressao and res_y.convergiu:
            return ResultadoBolha(P, y, S, it, True)
        if it < cfg.max_iter_pressao:
            P = P_novo

    return ResultadoBolha(P, y, S, cfg.max_iter_pressao, False)
