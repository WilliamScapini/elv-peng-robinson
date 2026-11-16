"""Históricos numéricos e exportação CSV compatível com planilhas."""
import csv
import math
import os

class Registro:
    def __init__(self, ativo=True, detalhado=False):
        self.ativo = ativo
        self.detalhado = detalhado
        self._tabelas = {}     # nome do loop -> lista de linhas (dict)

    def adicionar(self, nome, linha):
        if self.ativo:
            self._tabelas.setdefault(nome, []).append(linha)

    def linhas(self, nome):
        return self._tabelas.get(nome, [])

    def limpar(self, nome):
        """Retira resultados finais que não satisfizeram todos os critérios."""
        self._tabelas.pop(nome, None)

    def salvar_csvs(self, pasta, separador=",", decimal="."):
        """Grava <pasta>/<nome>.csv para cada loop. Devolve {nome: caminho}."""
        os.makedirs(pasta, exist_ok=True)
        caminhos = {}
        for nome, linhas in self._tabelas.items():
            colunas = _colunas(linhas)
            caminho = os.path.join(pasta, nome + ".csv")
            # utf-8-sig: o Excel reconhece os acentos
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                escritor = csv.writer(arquivo, delimiter=separador)
                escritor.writerow(colunas)
                for linha in linhas:
                    escritor.writerow([_formatar(linha.get(c, ""), decimal) for c in colunas])
            caminhos[nome] = caminho
        return caminhos



def _colunas(linhas):
    """União das chaves, na ordem em que aparecem pela primeira vez."""
    colunas = []
    for linha in linhas:
        for chave in linha:
            if chave not in colunas:
                colunas.append(chave)
    return colunas



def _formatar(valor, decimal):
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, float):
        if math.isnan(valor):
            return "nan"
        if math.isinf(valor):
            return "inf" if valor > 0 else "-inf"
        return ("%.12g" % valor).replace(".", decimal)
    return str(valor)
