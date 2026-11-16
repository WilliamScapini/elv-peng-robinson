"""Raízes reais de uma cúbica mônica pelo método de Cardano."""
import math
from dataclasses import dataclass

TOLERANCIA_DISCRIMINANTE = 1e-12

@dataclass(frozen=True)
class SolucaoCardano:
    """Tudo o que o método calcula, para poder ser registrado em CSV/HTML."""
    a2: float
    a1: float
    a0: float
    deslocamento: float      # -a2/3  (x = t + deslocamento)
    p: float
    q: float
    discriminante: float
    caso: str                # descrição de quantas raízes reais existem
    raizes: tuple            # raízes reais, em ordem crescente



def raiz_cubica_real(valor):
    """Raiz cúbica real (aceita valores negativos, ao contrário de valor ** (1/3))."""
    return math.copysign(abs(valor) ** (1.0 / 3.0), valor)



def _raiz_unica(p, q, delta):
    """
    Δ > 0: t = u + v, com u = ∛(-q/2 + √Δ) e v = ∛(-q/2 - √Δ).

    Forma numericamente estável: um dos dois radicandos quase se cancela
    (perde precisão). Calcula-se só o que não cancela (mesmo sinal de -q/2)
    e o outro sai de u·v = -p/3.
    """
    w = -q / 2.0 - math.copysign(math.sqrt(delta), q)
    u = raiz_cubica_real(w)
    v = -p / (3.0 * u) if u != 0.0 else 0.0
    return [u + v]



def _raizes_com_repeticao(p, q):
    """Δ = 0: uma raiz simples 3q/p e uma raiz dupla -3q/(2p)."""
    if p == 0.0:
        return [0.0, 0.0, 0.0]
    return [3.0 * q / p, -3.0 * q / (2.0 * p), -3.0 * q / (2.0 * p)]



def _raizes_trigonometricas(p, q):
    """Δ < 0: t_k = 2·√(-p/3)·cos( arccos( 3q/(2p)·√(-3/p) )/3 - 2πk/3 ), k = 0, 1, 2."""
    raio = 2.0 * math.sqrt(-p / 3.0)
    argumento = (3.0 * q / (2.0 * p)) * math.sqrt(-3.0 / p)
    argumento = max(-1.0, min(1.0, argumento))      # protege arccos de erro de arredondamento
    angulo = math.acos(argumento) / 3.0
    return [raio * math.cos(angulo - 2.0 * math.pi * k / 3.0) for k in range(3)]



def resolver_cubica(a2, a1, a0):
    """Resolve x³ + a2·x² + a1·x + a0 = 0 e devolve uma SolucaoCardano."""
    deslocamento = -a2 / 3.0
    p = a1 - a2 ** 2 / 3.0
    q = 2.0 * a2 ** 3 / 27.0 - a2 * a1 / 3.0 + a0
    delta = (q / 2.0) ** 2 + (p / 3.0) ** 3

    escala = max((q / 2.0) ** 2, abs((p / 3.0) ** 3), 1e-300)
    limite = TOLERANCIA_DISCRIMINANTE * escala

    if delta > limite:
        caso = "1 raiz real"
        t = _raiz_unica(p, q, delta)
    elif delta < -limite:
        caso = "3 raízes reais distintas"
        t = _raizes_trigonometricas(p, q)
    else:
        caso = "3 raízes reais (2 ou 3 iguais)"
        t = _raizes_com_repeticao(p, q)

    raizes = tuple(sorted(ti + deslocamento for ti in t))
    return SolucaoCardano(a2, a1, a0, deslocamento, p, q, delta, caso, raizes)
