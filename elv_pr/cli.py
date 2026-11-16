"""Interface de linha de comando e coordenação dos módulos científicos."""
import argparse
import html
import math
import sys
import webbrowser
from dataclasses import replace
from pathlib import Path

from . import __version__
from .ajuste import resolver, calcular_grade_objetivo
from .configuracao import carregar_configuracao
from .diagrama import calcular_diagrama_pxy
from .eos import ErroDeCalculo
from .estilos import CSS
from .formatacao import tabela
from .graficos import grafico_pxy_svg
from .proveniencia import metadados, salvar_json, hash_arquivo
from .registro import Registro
from .relatorio import gerar_relatorio


RAIZ = Path(__file__).resolve().parent.parent


def _resumo(solucao, registro, curvas):
    linhas = registro.linhas("pontos_experimentais")
    def numero(valor):
        return valor if math.isfinite(valor) else None
    return {
        "convergiu": solucao.convergiu,
        "k12": solucao.k12, "F": numero(solucao.F),
        "avaliacoes_k12": solucao.avaliacao_final,
        "desvio_medio_P_pct": sum(p["erro_P_pct"] for p in linhas)/len(linhas) if linhas else None,
        "desvio_medio_y1": sum(p["erro_y1_pontos_percentuais"] for p in linhas)/len(linhas)/100 if linhas else None,
        "pontos_diagrama": len(curvas), "falhas_diagrama": sum(p is None for p in curvas),
        "k12_proximo_limite": solucao.nos_limites,
    }


def _relatorio_comparacao(caminho, cfg, resultados, linhas):
    titulo = html.escape(" + ".join(s.nome for s in cfg.problema.substancias))
    fonte = html.escape(cfg.dados.get("fonte_dados", "Fonte não informada na entrada."))
    corpo = [f"<h1>ELV de {titulo}</h1>",
             f"<p>T = {cfg.problema.T:g} K. Software versão {__version__}.</p>",
             f"<p>Fonte dos dados experimentais: {fonte}</p>",
             "<p>O ajuste usa os pontos da própria isoterma. Os desvios apresentados descrevem essa correlação.</p>"]
    resumos = []
    for nome, (_, _, _, resumo) in resultados.items():
        resumos.append({
            "cenario": nome, "convergiu": resumo["convergiu"],
            "k12": f'{resumo["k12"]:.8f}',
            "F": f'{resumo["F"]:.5f}' if resumo["F"] is not None else "—",
            "desvio_medio_P_pct": f'{resumo["desvio_medio_P_pct"]:.3f}' if resumo["desvio_medio_P_pct"] is not None else "—",
            "desvio_medio_y1": f'{resumo["desvio_medio_y1"]:.5f}' if resumo["desvio_medio_y1"] is not None else "—",
        })
    corpo += ["<h2>Comparação dos cenários</h2>", tabela(resumos,
        ["cenario", "convergiu", "k12", "F", "desvio_medio_P_pct", "desvio_medio_y1"],
        ["Cenário", "Convergiu", "k₁₂", "F", "Desvio médio de P [%]", "Desvio médio de y₁ [fração]"], 9)]
    corpo += ['<h2>Diagramas P–x–y</h2><div class="two">']
    for nome, (solucao, registro, curvas, resumo) in resultados.items():
        corpo += [f'<div><h3>Cenário {nome}</h3>']
        if not solucao.convergiu:
            corpo += ["<p>O cálculo não convergiu. Consulte os históricos e as tolerâncias; os resultados finais deste cenário não são válidos.</p>"]
        if solucao.nos_limites:
            corpo += ["<p>O ajuste ficou próximo do limite de busca de k₁₂. Consulte o diagnóstico antes de interpretar o parâmetro como ótimo.</p>"]
        if curvas:
            corpo += [grafico_pxy_svg(curvas, cfg.problema, "linear", cfg.pontos)]
        if resumo["falhas_diagrama"]:
            corpo += [f'<p>Lacunas por falta de convergência: {resumo["falhas_diagrama"]}.</p>']
        if not cfg.diagrama.gerar:
            corpo += ['<p>Diagrama desativado na entrada.</p>']
        corpo += [f'<p><a href="{nome}/relatorio.html">Diagnóstico completo e históricos CSV</a></p></div>']
    corpo += ['</div><p>Linhas: bolha (x₁, azul) e orvalho (y₁, laranja). Círculos: dados experimentais.</p>']
    colunas = ["x1", "P_exp_atm", "y1_exp"]
    cabecalhos = ["x₁", "P experimental [atm]", "y₁ experimental"]
    for nome in resultados:
        colunas += [f"P_{nome}_atm", f"y1_{nome}"]
        cabecalhos += [f"P {nome} [atm]", f"y₁ {nome}"]
    linhas_formatadas = []
    for linha in linhas:
        linhas_formatadas.append({chave: (f"{valor:.3f}" if chave == "x1" or chave.startswith("P_") else f"{valor:.4f}")
                                  for chave, valor in linha.items()})
    corpo += ["<h2>Comparação por composição</h2>", tabela(linhas_formatadas, colunas, cabecalhos),
              '<p><a href="tabela_1.csv">Baixar tabela em CSV</a> · <a href="resumo.json">Resumo em JSON</a></p>',
              '<p class="footer"><a href="metadados.json">Identificação da versão, entrada e execução</a> · '
              '<a href="entrada_utilizada.json">Entrada utilizada</a>. CSVs e JSONs preservam mais algarismos.</p>']
    estilo_resumo = """
    .resumo h2 { margin:24px 0 12px; padding-top:10px; font-size:1.12rem; }
    .resumo h3 { margin:8px 0; }
    .resumo svg { display:block; width:100%; height:auto; }
    .resumo svg text, .resumo svg .small-title { font-size:20px; }
    .resumo .footer { margin-top:24px; }
    """
    pagina = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1">'
              f'<title>ELV de {titulo}</title><style>{CSS}{estilo_resumo}</style></head>'
              f'<body class="resumo"><main>{"".join(corpo)}</main></body></html>')
    caminho.write_text(pagina, encoding="utf-8")


def executar(cfg, pasta):
    """Produz resultados separados por cenário e a comparação das tabelas do artigo."""
    pasta.mkdir(parents=True, exist_ok=True)
    info = metadados(RAIZ, cfg)
    (pasta / "entrada_utilizada.json").write_bytes(cfg.conteudo_original)
    salvar_json(pasta / "metadados.json", info)
    cenarios = []
    if cfg.comparar_k12_zero:
        cenarios.append(("zero", replace(cfg.ajuste, ajustar=False, k12_fixo=0.0)))
    cenarios.append(("ajustado" if cfg.ajuste.ajustar else "fixo", cfg.ajuste))
    resultados = {}
    arquivos = [pasta / "entrada_utilizada.json"]
    linhas = [{"x1": x, "P_exp_atm": p, "y1_exp": y} for x, y, p in cfg.pontos]
    for nome, ajuste in cenarios:
        print(f"Calculando cenário {nome}...", flush=True)
        registro = Registro(detalhado=cfg.historico_detalhado_busca)
        solucao = resolver(cfg.problema, cfg.numerica, ajuste, registro, cfg.pontos)
        grade = calcular_grade_objetivo(cfg.problema, cfg.numerica, ajuste, registro, cfg.pontos) if solucao.convergiu else []
        curvas = calcular_diagrama_pxy(cfg.problema, cfg.numerica, cfg.diagrama,
                                      solucao.k12, registro, cfg.pontos) if solucao.convergiu else []
        destino = pasta / nome
        destino.mkdir(exist_ok=True)
        # Retira apenas saídas conhecidas da execução anterior deste cenário.
        for arquivo in ("loop_k12", "loop_pressao", "loop_y", "raizes_cardano",
                        "grade_objetivo", "diagrama_pxy", "pontos_experimentais"):
            (destino / f"{arquivo}.csv").unlink(missing_ok=True)
        csvs = registro.salvar_csvs(destino, cfg.saida.csv_separador, cfg.saida.csv_decimal)
        relatorio = destino / "relatorio.html"
        gerar_relatorio(relatorio, cfg.problema, ajuste, cfg.numerica, solucao,
                        registro, csvs, grade, curvas, cfg.pontos)
        arquivos += [Path(p) for p in csvs.values()] + [relatorio]
        resumo = _resumo(solucao, registro, curvas)
        resultados[nome] = solucao, registro, curvas, resumo
        if solucao.convergiu:
            print(f"  k12 = {solucao.k12:.10f}; F = {solucao.F:.8f}; "
                  f"desvio médio de P = {resumo['desvio_medio_P_pct']:.5f} %; "
                  f"desvio médio de y1 = {resumo['desvio_medio_y1']:.7f}")
            for linha, ponto in zip(linhas, registro.linhas("pontos_experimentais")):
                linha.update({f"P_{nome}_atm": ponto["P_calc_atm"], f"y1_{nome}": ponto["y1_calc"]})
        else:
            print("  NÃO CONVERGIU. Verifique o relatório e os limites de iterações.")
        if resumo["falhas_diagrama"]:
            print(f"  Diagrama: {resumo['falhas_diagrama']} ponto(s) sem convergência.")
    comparacao = Registro()
    for linha in linhas:
        comparacao.adicionar("tabela_1", linha)
    comparacao.salvar_csvs(pasta, cfg.saida.csv_separador, cfg.saida.csv_decimal)
    salvar_json(pasta / "resumo.json", {nome: resultado[3] for nome, resultado in resultados.items()})
    _relatorio_comparacao(pasta / "relatorio.html", cfg, resultados, linhas)
    arquivos += [pasta / "tabela_1.csv", pasta / "resumo.json", pasta / "relatorio.html"]
    info["resultados"] = {nome: resultado[3] for nome, resultado in resultados.items()}
    info["saidas_sha256"] = {p.relative_to(pasta).as_posix(): hash_arquivo(p) for p in arquivos}
    salvar_json(pasta / "metadados.json", info)
    return all(r[3]["convergiu"] for r in resultados.values())


def main(argumentos=None):
    parser = argparse.ArgumentParser(description="ELV binário com Peng–Robinson, sem bibliotecas externas.")
    parser.add_argument("entrada", nargs="?", type=Path,
                        default=RAIZ / "dados" / "etanol_agua_200C.json", help="arquivo JSON de entrada")
    parser.add_argument("--saida", type=Path, help="pasta dos resultados; padrão: campo saida.pasta relativo ao projeto")
    parser.add_argument("--sem-navegador", action="store_true", help="não abrir o relatório automaticamente")
    parser.add_argument("--validar", action="store_true", help="somente verificar o JSON, sem calcular")
    parser.add_argument("--versao", action="version", version=__version__)
    args = parser.parse_args(argumentos)
    try:
        cfg = carregar_configuracao(args.entrada)
        if args.validar:
            print(f"Entrada válida: {len(cfg.pontos)} ponto(s) a {cfg.problema.T:g} K.")
            return 0
        pasta = (args.saida if args.saida is not None else RAIZ / cfg.saida.pasta).resolve()
        convergiu = executar(cfg, pasta)
    except (OSError, ValueError, ArithmeticError, ErroDeCalculo) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    caminho = pasta / "relatorio.html"
    print(f"Relatório: {caminho}")
    if not args.sem_navegador:
        webbrowser.open(caminho.as_uri())
    return 0 if convergiu else 1
