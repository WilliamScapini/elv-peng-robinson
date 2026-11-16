"""Dados imutáveis do problema e configurações numéricas, com unidades explícitas."""
from dataclasses import dataclass, replace
import math

@dataclass(frozen=True)
class Substancia:
    nome: str
    formula: str
    Tc: float        # temperatura crítica [K]
    Pc: float        # pressão crítica [atm]
    w: float         # fator acêntrico [-]



@dataclass(frozen=True)
class Problema:
    substancias: tuple
    R: float             # constante dos gases [atm·L/(K·mol)]
    T: float             # temperatura experimental [K]
    x: tuple             # composição líquida do primeiro ponto
    P_exp: float         # pressão experimental [atm]
    y_exp: tuple         # composição experimental do vapor
    correlacao_m: str    # "planilha" ou "peng_robinson" (ver fator_m na seção 3)
    P_inicial: float     # chute inicial de pressão [atm]
    y_inicial: tuple     # chute inicial da composição do vapor



@dataclass(frozen=True)
class ConfigNumerica:
    tol_y: float             # loop do vapor: erro máximo entre duas iterações de y
    max_iter_y: int
    tol_pressao: float       # loop da pressão: |Σ K_i·x_i - 1|
    max_iter_pressao: int
    tol_k12: float           # loop do k12: largura do intervalo de busca
    max_aval_k12: int        # máximo de avaliações de k12
    n_pontos_grade_f: int    # número de pontos calculados na grade adicional de F(k12)



@dataclass(frozen=True)
class ConfigK12:
    ajustar: bool        # True: ajusta k12 aos dados experimentais; False: usa k12_fixo
    k12_fixo: float
    k12_min: float       # intervalo de busca do k12
    k12_max: float



@dataclass(frozen=True)
class ConfigSaida:
    pasta: str               # criada ao lado dos arquivos .py
    csv_separador: str       # "," padrão; use ";" se abrir direto no Excel em português
    csv_decimal: str         # "." padrão; use "," junto com ";" no Excel em português



@dataclass(frozen=True)
class ConfigDiagramaPxy:
    gerar: bool
    n_pontos: int  # número de composições líquidas entre 0 e 1



def preparar_pontos(problema, pontos):
    if not pontos:
        raise ValueError("Informe pelo menos um ponto experimental.")
    resultado = []
    for x1, y1, P in pontos:
        if not all(math.isfinite(v) for v in (x1, y1, P)) or not (0 <= x1 <= 1 and 0 <= y1 <= 1 and P > 0):
            raise ValueError("Cada ponto deve ter 0 <= x1,y1 <= 1 e P > 0, com valores finitos.")
        resultado.append(replace(problema, x=(x1, 1-x1), y_exp=(y1, 1-y1),
                                 P_exp=P, P_inicial=P, y_inicial=(y1, 1-y1)))
    return resultado
