"""Equação de Peng–Robinson, regras de mistura e fugacidades."""
import math
from dataclasses import dataclass
from .cardano import SolucaoCardano, resolver_cubica

RAIZ2 = math.sqrt(2.0)
CONSTANTE_A = 0.45724
CONSTANTE_B = 0.07780
LIMITE_FASES_IGUAIS = 1e-6

class ErroDeCalculo(Exception):
    """Falha numérica (por exemplo, nenhuma raiz fisicamente válida)."""



@dataclass(frozen=True)
class ParametrosPuro:
    nome: str
    Tr: float        # T / Tc
    m: float
    alfa: float      # α(T)
    a: float         # [L²·atm/mol²]
    b: float         # [L/mol]



@dataclass(frozen=True)
class Sistema:
    """Mistura a uma temperatura e a um k12 fixos (não depende de P nem de composição)."""
    T: float
    R: float
    k12: float
    puros: tuple     # ParametrosPuro de cada componente
    a_ij: tuple      # matriz a_ij = (1 - k_ij)·√(a_i·a_j)

    @property
    def n(self):
        return len(self.puros)



@dataclass(frozen=True)
class ResultadoFase:
    fase: str            # "liquido" ou "vapor"
    z: tuple             # composição da fase
    P: float
    a_mist: float
    b_mist: float
    A: float
    B: float
    cardano: SolucaoCardano
    Z: float             # raiz escolhida
    termos: tuple        # um dict por componente (ver termos_fugacidade)

    @property
    def phi(self):
        return tuple(t["phi"] for t in self.termos)

    @property
    def ln_phi(self):
        return tuple(t["ln_phi"] for t in self.termos)



def fator_m(w, correlacao):
    """Fator m(ω) de α(T) = [1 + m·(1 - √Tr)]²."""
    if correlacao == "planilha":
        return 0.48 + 1.574 * w - 0.176 * w ** 2
    if correlacao == "peng_robinson":
        return 0.37464 + 1.54226 * w - 0.26992 * w ** 2
    raise ValueError("correlacao_m deve ser 'planilha' ou 'peng_robinson'")



def parametros_puro(substancia, T, R, correlacao_m):
    Tr = T / substancia.Tc
    m = fator_m(substancia.w, correlacao_m)
    alfa = (1.0 + m * (1.0 - math.sqrt(Tr))) ** 2
    a = CONSTANTE_A * R ** 2 * substancia.Tc ** 2 / substancia.Pc * alfa
    b = CONSTANTE_B * R * substancia.Tc / substancia.Pc
    return ParametrosPuro(substancia.nome, Tr, m, alfa, a, b)



def montar_sistema(substancias, T, R, k12, correlacao_m):
    """Calcula a_i, b_i e a matriz a_ij (binário: k11 = k22 = 0 e k12 = k21)."""
    if len(substancias) != 2:
        raise ValueError("Este programa trata misturas binárias (um único k12).")
    puros = tuple(parametros_puro(s, T, R, correlacao_m) for s in substancias)
    kij = ((0.0, k12), (k12, 0.0))
    a_ij = tuple(
        tuple((1.0 - kij[i][j]) * math.sqrt(puros[i].a * puros[j].a) for j in range(2))
        for i in range(2)
    )
    return Sistema(T, R, k12, puros, a_ij)



def regras_de_mistura(sistema, z):
    """a = ΣΣ z_i·z_j·a_ij   e   b = Σ z_i·b_i."""
    n = sistema.n
    a_mist = sum(z[i] * z[j] * sistema.a_ij[i][j] for i in range(n) for j in range(n))
    b_mist = sum(z[i] * sistema.puros[i].b for i in range(n))
    return a_mist, b_mist



def coeficientes_cubica(A, B):
    """Z³ - (1-B)·Z² + (A - 2B - 3B²)·Z - (AB - B² - B³) = 0  ->  (a2, a1, a0)."""
    a2 = -(1.0 - B)
    a1 = A - 2.0 * B - 3.0 * B ** 2
    a0 = -(A * B - B ** 2 - B ** 3)
    return a2, a1, a0



def escolher_raiz(raizes, B, fase):
    """Entre as raízes com Z > B (necessário para ln(Z-B)): líquido = menor, vapor = maior."""
    validas = [z for z in raizes if z > B]
    if not validas:
        raise ErroDeCalculo("nenhuma raiz da cúbica satisfaz Z > B")
    return min(validas) if fase == "liquido" else max(validas)



def termos_fugacidade(sistema, z, i, a_mist, b_mist, A, B, Z):
    """
    ln φ_i = (b_i/b)(Z-1) - ln(Z-B) + A/(2√2·B) · [2·Σ_k z_k·a_ki / a - b_i/b] · ln[(Z+(1-√2)B)/(Z+(1+√2)B)]

    Os nomes dos termos são os da planilha. "termo2" é ln(Z-B) (entra subtraindo).
    """
    b_i = sistema.puros[i].b
    soma_za = sum(z[k] * sistema.a_ij[k][i] for k in range(sistema.n))

    termo1 = (b_i / b_mist) * (Z - 1.0)
    termo2 = math.log(Z - B)
    termo3a = A / (2.0 * RAIZ2 * B)
    termo3b = 2.0 * soma_za / a_mist - b_i / b_mist
    termo3c = math.log((Z + (1.0 - RAIZ2) * B) / (Z + (1.0 + RAIZ2) * B))
    termo3 = termo3a * termo3b * termo3c
    ln_phi = termo1 - termo2 + termo3

    return {
        "termo1": termo1, "termo2": termo2,
        "termo3a": termo3a, "termo3b": termo3b, "termo3c": termo3c, "termo3": termo3,
        "ln_phi": ln_phi, "phi": math.exp(ln_phi),
    }



def calcular_fase(sistema, z, fase, P):
    """Dado (T, P, composição z), calcula Z e os coeficientes de fugacidade da fase."""
    RT = sistema.R * sistema.T
    a_mist, b_mist = regras_de_mistura(sistema, z)
    A = a_mist * P / RT ** 2
    B = b_mist * P / RT

    a2, a1, a0 = coeficientes_cubica(A, B)
    cardano = resolver_cubica(a2, a1, a0)
    Z = escolher_raiz(cardano.raizes, B, fase)

    termos = tuple(
        termos_fugacidade(sistema, z, i, a_mist, b_mist, A, B, Z) for i in range(sistema.n)
    )
    return ResultadoFase(fase, tuple(z), P, a_mist, b_mist, A, B, cardano, Z, termos)
