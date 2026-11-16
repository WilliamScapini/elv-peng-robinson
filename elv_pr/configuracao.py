"""Leitura e validação das entradas JSON antes de iniciar os cálculos."""
import json
import math
from dataclasses import dataclass, fields
from pathlib import Path

from .modelos import (
    Substancia, Problema, ConfigNumerica, ConfigK12, ConfigSaida,
    ConfigDiagramaPxy, preparar_pontos,
)


@dataclass(frozen=True)
class Configuracao:
    problema: Problema
    pontos: tuple
    numerica: ConfigNumerica
    ajuste: ConfigK12
    saida: ConfigSaida
    diagrama: ConfigDiagramaPxy
    comparar_k12_zero: bool
    historico_detalhado_busca: bool
    dados: dict
    conteudo_original: bytes


PADRAO_NUMERICO = dict(
    tol_y=1e-12, max_iter_y=200, tol_pressao=1e-10,
    max_iter_pressao=100, tol_k12=1e-6, max_aval_k12=100,
    n_pontos_grade_f=101,
)


def _objeto(valor, nome, permitidos, obrigatorios=()):
    if not isinstance(valor, dict):
        raise ValueError(f"{nome}: informe um objeto JSON entre chaves.")
    extras = set(valor) - set(permitidos)
    faltantes = set(obrigatorios) - set(valor)
    if extras:
        raise ValueError(f"{nome}: campos desconhecidos: {', '.join(sorted(extras))}.")
    if faltantes:
        raise ValueError(f"{nome}: faltam os campos: {', '.join(sorted(faltantes))}.")


def _numero(valor, nome, positivo=False):
    if type(valor) not in (int, float) or not math.isfinite(valor):
        raise ValueError(f"{nome}: informe um número finito, com ponto decimal.")
    if positivo and valor <= 0:
        raise ValueError(f"{nome}: o valor deve ser maior que zero.")


def _inteiro(valor, nome, minimo):
    if type(valor) is not int or valor < minimo:
        raise ValueError(f"{nome}: informe um inteiro maior ou igual a {minimo}.")


def _booleano(valor, nome):
    if type(valor) is not bool:
        raise ValueError(f"{nome}: use true ou false, sem aspas.")


def _texto(valor, nome):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{nome}: informe um texto não vazio.")


def _sem_duplicatas(pares):
    resultado = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"Campo JSON repetido: {chave}.")
        resultado[chave] = valor
    return resultado


def _constante_invalida(valor):
    raise ValueError(f"{valor} não é um número válido em JSON.")


def _config(classe, valor, padrao, nome):
    _objeto(valor, nome, [f.name for f in fields(classe)])
    return classe(**dict(padrao, **valor))


def carregar_configuracao(caminho):
    """Não executa código do arquivo: aceita apenas dados JSON validados."""
    conteudo = Path(caminho).read_bytes()
    try:
        dados = json.loads(conteudo.decode("utf-8-sig"),
                           object_pairs_hook=_sem_duplicatas,
                           parse_constant=_constante_invalida)
    except (json.JSONDecodeError, UnicodeDecodeError) as erro:
        raise ValueError(f"JSON inválido em {caminho}: {erro}") from erro
    _objeto(dados, "entrada", (
        "titulo", "fonte_dados", "substancias", "condicoes", "pontos_experimentais",
        "numerica", "ajuste_k12", "saida", "diagrama_pxy", "comparar_k12_zero",
        "historico_detalhado_busca",
    ), ("substancias", "condicoes", "pontos_experimentais"))
    for nome in ("titulo", "fonte_dados"):
        if nome in dados:
            _texto(dados[nome], nome)
    substancias = dados["substancias"]
    if not isinstance(substancias, list) or len(substancias) != 2:
        raise ValueError("substancias: informe exatamente dois componentes, na ordem 1 e 2.")
    componentes = []
    for i, item in enumerate(substancias, 1):
        nome = f"substancias[{i}]"
        chaves = ("nome", "formula", "Tc_K", "Pc_atm", "omega")
        _objeto(item, nome, chaves, chaves)
        for chave in ("nome", "formula"):
            _texto(item[chave], f"{nome}.{chave}")
        for chave in ("Tc_K", "Pc_atm", "omega"):
            _numero(item[chave], f"{nome}.{chave}", positivo=chave != "omega")
        componentes.append(Substancia(item["nome"], item["formula"],
                                     item["Tc_K"], item["Pc_atm"], item["omega"]))
    condicoes = dados["condicoes"]
    _objeto(condicoes, "condicoes", ("T_K", "R_atm_L_mol_K", "correlacao_m"), ("T_K",))
    T = condicoes["T_K"]
    R = condicoes.get("R_atm_L_mol_K", 0.08205)
    _numero(T, "T_K", positivo=True)
    _numero(R, "R_atm_L_mol_K", positivo=True)
    correlacao = condicoes.get("correlacao_m", "peng_robinson")
    if correlacao not in ("planilha", "peng_robinson"):
        raise ValueError("correlacao_m: use 'peng_robinson' ou 'planilha'.")
    pontos = dados["pontos_experimentais"]
    if not isinstance(pontos, list) or not pontos:
        raise ValueError("pontos_experimentais: informe pelo menos um ponto da isoterma.")
    valores = []
    for i, ponto in enumerate(pontos, 1):
        nome = f"pontos_experimentais[{i}]"
        _objeto(ponto, nome, ("x1", "y1", "P_atm"), ("x1", "y1", "P_atm"))
        for chave in ("x1", "y1", "P_atm"):
            _numero(ponto[chave], f"{nome}.{chave}", positivo=chave == "P_atm")
        if not (0 <= ponto["x1"] <= 1 and 0 <= ponto["y1"] <= 1):
            raise ValueError(f"{nome}: x1 e y1 devem estar entre 0 e 1.")
        if ponto["x1"] in (0, 1):
            raise ValueError(f"{nome}: use 0 < x1 < 1 no ajuste; os puros são calculados no diagrama.")
        valores.append((ponto["x1"], ponto["y1"], ponto["P_atm"]))
    x, y, p = valores[0]
    problema = Problema(tuple(componentes), R, T, (x, 1-x), p, (y, 1-y),
                        correlacao, p, (y, 1-y))
    preparar_pontos(problema, valores)
    numerica = _config(ConfigNumerica, dados.get("numerica", {}), PADRAO_NUMERICO, "numerica")
    for nome in ("tol_y", "tol_pressao", "tol_k12"):
        _numero(getattr(numerica, nome), nome, positivo=True)
    for nome in ("max_iter_y", "max_iter_pressao", "max_aval_k12"):
        _inteiro(getattr(numerica, nome), nome, 3 if nome == "max_aval_k12" else 1)
    _inteiro(numerica.n_pontos_grade_f, "n_pontos_grade_f", 0)
    if numerica.n_pontos_grade_f in (1, 2):
        raise ValueError("n_pontos_grade_f: use 0 para desativar, ou pelo menos 3.")
    ajuste = _config(ConfigK12, dados.get("ajuste_k12", {}),
                     dict(ajustar=True, k12_fixo=0.0, k12_min=-0.5, k12_max=0.5), "ajuste_k12")
    _booleano(ajuste.ajustar, "ajustar")
    for nome in ("k12_fixo", "k12_min", "k12_max"):
        _numero(getattr(ajuste, nome), nome)
    if ajuste.ajustar and ajuste.k12_min >= ajuste.k12_max:
        raise ValueError("k12_min deve ser menor que k12_max para ajustar k12.")
    saida = _config(ConfigSaida, dados.get("saida", {}),
                    dict(pasta="resultados", csv_separador=",", csv_decimal="."), "saida")
    _texto(saida.pasta, "saida.pasta")
    if saida.csv_separador not in (",", ";", "\t") or saida.csv_decimal not in (".", ","):
        raise ValueError("CSV: separador deve ser vírgula, ponto e vírgula ou tabulação; decimal deve ser '.' ou ','.")
    if saida.csv_separador == saida.csv_decimal:
        raise ValueError("CSV: separador e símbolo decimal devem ser diferentes.")
    diagrama = _config(ConfigDiagramaPxy, dados.get("diagrama_pxy", {}),
                       dict(gerar=True, n_pontos=61), "diagrama_pxy")
    _booleano(diagrama.gerar, "diagrama_pxy.gerar")
    _inteiro(diagrama.n_pontos, "diagrama_pxy.n_pontos", 2)
    comparar = dados.get("comparar_k12_zero", True)
    detalhado = dados.get("historico_detalhado_busca", False)
    _booleano(comparar, "comparar_k12_zero")
    _booleano(detalhado, "historico_detalhado_busca")
    return Configuracao(problema, tuple(valores), numerica, ajuste, saida,
                        diagrama, comparar, detalhado, dados, conteudo)
