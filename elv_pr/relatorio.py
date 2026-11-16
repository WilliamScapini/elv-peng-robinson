"""Relatório didático HTML com entradas, resultados e diagnóstico."""
import html
import os
from datetime import datetime
from .estilos import CSS
from .formatacao import fmt, tabela, tabela_pares, cartao, aviso
from .graficos import grafico_pressao_svg, grafico_objetivo_svg, grafico_fugacidades_svg, grafico_pxy_svg

def secao_resumo(problema, ajuste, sol):
    if not sol.convergiu:
        return aviso("<b>O cálculo não convergiu.</b> Os resultados termodinâmicos finais não devem ser interpretados como equilíbrio. "
                     "Consulte os históricos CSV para localizar o loop que interrompeu.", "error")
    dif_f = sum(abs(a-b) for a,b in zip(sol.f_liquido,sol.f_vapor))
    cartoes = [
        cartao("k₁₂ " + ("ajustado" if ajuste.ajustar else "fixo"), fmt(sol.k12,8),
               "k₁₁ = k₂₂ = 0; k₁₂ = k₂₁"),
        cartao("Pressão calculada", fmt(sol.P,8) + " atm",
               "experimental: %s atm · erro: %s%%" % (fmt(problema.P_exp),fmt(sol.dP_pct,5))),
        cartao("y₁ calculado", fmt(sol.y[0],8),
               "experimental: %s · erro: %s pontos percentuais" % (fmt(problema.y_exp[0]),fmt(sol.dy1_pct,5))),
        cartao("Σ |fᴸ − fⱽ|", "%.3e atm" % dif_f,
               "soma das diferenças absolutas dos componentes"),
    ]
    return '<div class="cards">%s</div>' % "".join(cartoes)



def secao_avisos(problema, ajuste, sol):
    textos = []
    if problema.correlacao_m == "planilha":
        textos.append(aviso(
            "<b>Correlação do fator m:</b> o cálculo manteve a expressão da planilha, "
            "<code>m = 0,48 + 1,574·ω − 0,176·ω²</code>. Ela não é a correlação original de Peng–Robinson. "
            "A forma original é <code>m = 0,37464 + 1,54226·ω − 0,26992·ω²</code>. "
            "A equação de estado continua sendo Peng–Robinson; o que muda é a correlação usada em α(T).", "warn"))
    if sol.nos_limites:
        textos.append(aviso("O k₁₂ ajustado ficou muito próximo de uma extremidade do intervalo de busca "
                            "[%s; %s]. Isso pode indicar que o intervalo precisa ser ampliado." %
                            (fmt(ajuste.k12_min),fmt(ajuste.k12_max)), "warn"))
    if sol.convergiu and abs(sol.fase_liquida.Z-sol.fase_vapor.Z) < 1e-9:
        textos.append(aviso("Os fatores Z das fases ficaram praticamente iguais; verifique se o estado calculado não é uma solução trivial.","error"))
    textos.append(aviso(
        "<b>Escopo do ajuste:</b> k₁₂ é calibrado com os pontos experimentais fornecidos na mesma temperatura. "
        "A concordância com esses dados não valida, por si só, previsões fora das condições medidas.", ""))
    return "".join(textos)



def secao_objetivo():
    return ("<h2>1. O que o cálculo procura</h2>"
            "<p>Para a temperatura e a composição líquida informadas, o problema é encontrar a pressão de bolha "
            "e a composição do vapor que satisfaçam o equilíbrio líquido–vapor. Em seguida, o parâmetro de interação "
            "binária k₁₂ é ajustado para aproximar a pressão calculada e a composição de vapor experimental.</p>"
            '<div class="flow">'
            '<div class="flow-item"><strong>1 · Ajuste externo de k₁₂</strong>'
            'A busca por seção áurea testa valores de k₁₂ e minimiza a função objetivo F.</div>'
            '<div class="flow-item"><strong>2 · Pressão de bolha</strong>'
            'Para cada k₁₂, atualiza P até que S = Σ Kᵢxᵢ se aproxime de 1.</div>'
            '<div class="flow-item"><strong>3 · Composição do vapor</strong>'
            'Para cada pressão, atualiza y até que a maior variação entre duas iterações seja menor que a tolerância.</div>'
            '</div>'
            '<div class="eq">ΔP% = 100·|Pcalc − Pexp|/Pexp &nbsp;&nbsp; · &nbsp;&nbsp; Δy₁ = 100·|y₁,calc − y₁,exp| (pontos percentuais)</div>'
            '<div class="eq">F(k₁₂) = média dos pontos de [(ΔP%)² + (Δy₁)²]</div>'
            '<p>O erro da pressão é relativo; o de composição é em pontos percentuais. Os quadrados entram com o mesmo peso, e todos os pontos experimentais têm o mesmo peso. A seção áurea reduz o intervalo de busca supondo que exista um vale único no intervalo informado.</p>'
            '<p>Em cada avaliação, a equação de Peng–Robinson é resolvida para as fases líquida e vapor. '
            'A cúbica em Z é resolvida por Cardano e os coeficientes de fugacidade são usados para obter Kᵢ = φᵢᴸ/φᵢⱽ.</p>')



def secao_equacoes(problema):
    if problema.correlacao_m == "planilha":
        expr_m = "m = 0,48 + 1,574·ω − 0,176·ω²"
    else:
        expr_m = "m = 0,37464 + 1,54226·ω − 0,26992·ω²"
    return ("<h2>2. Modelo termodinâmico</h2>"
            '<div class="eq">α(T) = [1 + m(1 − √(T/Tc))]²</div>'
            '<div class="eq">aᵢⱼ = (1 − kᵢⱼ)√(aᵢaⱼ) ··· aₘ = ΣᵢΣⱼ zᵢzⱼaᵢⱼ ··· bₘ = Σᵢ zᵢbᵢ</div>'
            '<div class="eq">Kᵢ = φᵢᴸ/φᵢⱽ ··· yᵢ = Kᵢxᵢ / ΣⱼKⱼxⱼ ··· S = ΣᵢKᵢxᵢ → 1</div>'
            '<div class="eq">fᵢᴸ = φᵢᴸxᵢP   e   fᵢⱽ = φᵢⱽyᵢP; no equilíbrio, fᵢᴸ = fᵢⱽ para cada componente.</div>'
            '<p>O fator m utilizado neste cálculo é <code>%s</code>. As regras de mistura usam k₁₁ = k₂₂ = 0 e '
            'k₁₂ = k₂₁. O parâmetro k₁₂ modifica o termo atrativo cruzado entre os componentes.</p>' % html.escape(expr_m))



def secao_entrada(problema, ajuste, cfg):
    comp = [{"Componente": "%s (%s)" % (s.nome,s.formula), "Tc":s.Tc,"Pc":s.Pc,"omega":s.w}
            for s in problema.substancias]
    t_comp = tabela(comp,["Componente","Tc","Pc","omega"],["Componente","Tc [K]","Pc [atm]","ω"])
    cond = [
        ("Constante dos gases R [atm·L/(K·mol)]",problema.R),
        ("Temperatura experimental [K]",problema.T),
        ("Pressão experimental do primeiro ponto [atm]",problema.P_exp),
        ("Composição líquida x do primeiro ponto",", ".join(fmt(v) for v in problema.x)),
        ("Composição experimental do vapor y do primeiro ponto",", ".join(fmt(v) for v in problema.y_exp)),
        ("Correlação de m",problema.correlacao_m),
        ("Pressão inicial [atm]",problema.P_inicial),
        ("Composição inicial do vapor",", ".join(fmt(v) for v in problema.y_inicial)),
    ]
    num = [
        ("Ajustar k₁₂",ajuste.ajustar),
        ("Intervalo de busca" if ajuste.ajustar else "k₁₂ fixo",
         "[%s; %s]" % (fmt(ajuste.k12_min),fmt(ajuste.k12_max)) if ajuste.ajustar else ajuste.k12_fixo),
        ("Tolerância de y",cfg.tol_y),
        ("Tolerância de pressão |S−1|",cfg.tol_pressao),
        ("Tolerância da busca em k₁₂",cfg.tol_k12),
        ("Pontos na grade adicional de F",cfg.n_pontos_grade_f),
        ("Máximo de avaliações de k₁₂",cfg.max_aval_k12),
    ]
    return ('<div class="two"><div><h3>Componentes</h3>%s<h3>Condições experimentais</h3>%s</div>'
            '<div><h3>Configuração numérica</h3>%s</div></div>' % (t_comp,tabela_pares(cond),tabela_pares(num)))



def secao_puros(sol):
    linhas = [{"Componente":p.nome,"Tr":p.Tr,"m":p.m,"alpha":p.alfa,"a":p.a,"b":p.b}
              for p in sol.sistema.puros]
    return tabela(linhas,["Componente","Tr","m","alpha","a","b"],
                  ["Componente","Tr","m","α(T)","a [L²·atm/mol²]","b [L/mol]"],8)



def secao_convergencia(sol, registro, grade, cfg):
    k12 = registro.linhas("loop_k12")
    id_final = sol.avaliacao_final
    pressao = [l for l in registro.linhas("loop_pressao") if l.get("avaliacao_k12") == id_final and l.get("ponto_experimental") == 1]
    if not sol.convergiu:
        return aviso("Os gráficos de convergência final dependem de uma solução convergida; consulte os CSVs para analisar as avaliações interrompidas.","warn")

    g1 = grafico_pressao_svg(pressao,cfg.tol_pressao)
    g2 = grafico_objetivo_svg(grade,k12,sol.k12)
    if not grade:
        g2 = '<p class="muted">O ajuste de k₁₂ está desativado; não foi gerada a grade da função objetivo.</p>'
    bloco = ('<h2>3. Diagnóstico numérico</h2><div class="two">'
             '<div class="chart-card"><h3>Erro da pressão por iteração</h3><div class="chart">%s</div>'
             '<p>O critério de parada é |S − 1| menor que a tolerância. A escala logarítmica evidencia a redução do erro por ordens de grandeza.</p></div>'
             '<div class="chart-card"><h3>Função objetivo versus k₁₂</h3><div class="chart">%s</div>'
             '<div class="legend"><span><i class="swatch" style="background:var(--acento)"></i>Grade recalculada</span>'
             '<span><i class="swatch" style="background:var(--secundaria)"></i>Avaliações da seção áurea</span>'
             '<span><i class="swatch" style="background:var(--terciaria)"></i>Valor final</span></div>'
             '<p>A curva é formada por novas soluções do problema para cada k₁₂ da grade; os quadrados indicam os pontos realmente testados pela seção áurea.</p></div>'
             '</div>') % (g1,g2)

    cols_k = ["avaliacao","etapa","k12","P_calc_atm","y1_calc","dP_pct","dy1_pct","F","iteracoes_P","convergiu"]
    cols_p = ["iter_P","P_atm","Z_L","Z_V","iteracoes_y","y1","y2","K1","K2","S","erro_S_menos_1","P_novo_atm"]
    detalhe = ('<details><summary>Ver avaliações do ajuste de k₁₂ (%d registros)</summary>%s</details>' %
               (len(k12),tabela(k12,cols_k,digitos=9)))
    detalhe += ('<details><summary>Ver iterações da pressão para o k₁₂ final (%d registros)</summary>%s</details>' %
                (len(pressao),tabela(pressao,cols_p,digitos=9)))
    detalhe += '<p class="muted">O histórico detalhado do loop da composição y e das raízes da cúbica permanece nos arquivos CSV. O gráfico mostra o primeiro ponto experimental; o gráfico de y foi omitido para evitar redundância visual.</p>'
    return bloco + detalhe



def bloco_fase(res,titulo):
    c = res.cardano
    pares = [
        ("Z selecionado",res.Z), ("A",res.A), ("B",res.B),
        ("Coeficientes da cúbica (1, a₂, a₁, a₀)","1; %s; %s; %s" % (fmt(c.a2,10),fmt(c.a1,10),fmt(c.a0,10))),
        ("Discriminante de Cardano",c.discriminante),
        ("Raízes reais",", ".join(fmt(v,10) for v in c.raizes)),
    ]
    return '<div><h3>%s</h3>%s</div>' % (titulo,tabela_pares(pares,10))



def secao_fugacidades(problema,sol):
    if not sol.convergiu:
        return ""
    linhas=[]
    for i,sub in enumerate(problema.substancias):
        fl,fv=sol.f_liquido[i],sol.f_vapor[i]
        dif=abs(fl-fv)
        rel=dif/max(abs(fl),abs(fv),1e-300)*100
        linhas.append({"Componente":sub.nome+" ("+sub.formula+")","fL":fl,"fV":fv,"dif":dif,"rel":rel})
    soma=sum(abs(a-b) for a,b in zip(sol.f_liquido,sol.f_vapor))
    estado = tabela_pares([
        ("Temperatura",str(fmt(problema.T))+" K"),
        ("Pressão de bolha calculada",str(fmt(sol.P,10))+" atm"),
        ("Composição líquida x do primeiro ponto",", ".join(fmt(v,8) for v in problema.x)),
        ("Composição vapor calculada y",", ".join(fmt(v,8) for v in sol.y)),
        ("Fator de compressibilidade Zᴸ",sol.fase_liquida.Z),
        ("Fator de compressibilidade Zⱽ",sol.fase_vapor.Z),
    ])
    return ('<h2>4. Verificação do equilíbrio por fugacidade</h2>'
            '<p>Para cada componente, a condição de equilíbrio exige que a fugacidade na fase líquida seja igual à fugacidade na fase vapor. '
            'Cada componente recebe uma escala própria porque as magnitudes dos componentes podem ser diferentes; compare apenas o par líquido–vapor dentro de cada componente. Os valores numéricos absolutos aparecem na tabela.</p>'
            '<div class="chart-card"><div class="chart">%s</div>'
            '<div class="legend"><span><i class="swatch" style="background:var(--acento)"></i>Fase líquida</span>'
            '<span><i class="swatch" style="background:var(--secundaria)"></i>Fase vapor</span></div></div>'
            '<h3>Valores e diferenças</h3>%s'
            '<p class="muted">Σ|fᴸ − fⱽ| = %.4e atm. O cálculo de equilíbrio usa igualdade de fugacidades, não igualdade de pressões parciais.</p>'
            '<div class="two"><div><h3>Estado final</h3>%s</div><div><h3>Raízes de Cardano e estado das fases</h3><details><summary>Mostrar parâmetros das fases</summary><div class="two">%s%s</div></details></div></div>'
            % (grafico_fugacidades_svg(problema,sol),
               tabela(linhas,["Componente","fL","fV","dif","rel"],["Componente","fᴸ [atm]","fⱽ [atm]","|Δf| [atm]","erro relativo [%]"],10),
               soma,estado,bloco_fase(sol.fase_liquida,"Fase líquida"),bloco_fase(sol.fase_vapor,"Fase vapor")))



def secao_diagrama_pxy(problema, sol, pontos, registro, pontos_experimentais):
    if not pontos:
        return '<h2>5. Diagrama P–x–y</h2><p>Diagrama desativado ou cálculo principal não convergiu.</p>'
    falhas=sum(p is None for p in pontos)
    tabela_pontos = tabela(registro.linhas("pontos_experimentais"),
        ["ponto","x1","y1_exp","P_exp_atm","y1_calc","P_calc_atm","erro_P_pct","erro_y1_pontos_percentuais"],
        ["Ponto","x₁","y₁ experimental","P experimental [atm]","y₁ calculado","P calculada [atm]","Erro P [%]","Erro y₁ [pontos percentuais]"], 7)
    return (f'<h2>5. Diagrama P–x–y a {fmt(problema.T)} K</h2>'
        '<p>Linhas: bolha (x₁, azul) e orvalho (y₁, laranja). Círculos: dados experimentais. '
        'Cada par calculado representa fases em equilíbrio à mesma pressão.</p>'
        f'<p>Pontos sem convergência: {falhas}. Lacunas nas curvas representam cálculos sem solução confiável.</p>'
        '<div class="chart">'+grafico_pxy_svg(pontos,problema,"linear",pontos_experimentais)+'</div>'
        '<h3>Comparação dos pontos experimentais</h3>'+tabela_pontos)



def secao_parametros(sol):
    return ('<h2>6. Parâmetros calculados dos componentes puros</h2>'
            '<p class="muted">Valores usados para construir a e b de cada componente na temperatura do problema.</p>'
            + secao_puros(sol))



def secao_arquivos(caminhos_csv,registro):
    descricoes={
        "loop_k12":"Avaliações da busca por seção áurea; inclui o ponto final.",
        "loop_pressao":"Iterações de pressão em cada avaliação de k₁₂.",
        "loop_y":"Iterações da composição de vapor para cada pressão avaliada.",
        "raizes_cardano":"Coeficientes, discriminante, raízes reais e raiz Z selecionada em cada fase.",
        "grade_objetivo":"Recálculos independentes de F em uma grade uniforme de k₁₂.",
        "diagrama_pxy":"Pontos de bolha e orvalho na temperatura experimental.",
        "pontos_experimentais":"Comparação entre dados experimentais e calculados.",
    }
    linhas=[]
    for nome,caminho in caminhos_csv.items():
        arq=os.path.basename(caminho)
        link='<a href="%s">%s</a>' % (html.escape(arq,quote=True),html.escape(arq))
        linhas.append({"arquivo":link,"descricao":descricoes.get(nome,""),"linhas":len(registro.linhas(nome))})
    # O nome do arquivo é HTML intencional, então substituímos a célula desse campo após montar a tabela.
    cab = '<div class="table-scroll"><table><thead><tr><th>Arquivo</th><th>Conteúdo</th><th>Linhas</th></tr></thead><tbody>'
    for row in linhas:
        cab += '<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (row["arquivo"],html.escape(row["descricao"]),row["linhas"])
    return '<h2>8. Arquivos para auditoria</h2><p>Os CSVs preservam o histórico que não precisa ficar exposto em tabelas extensas no corpo do relatório.</p>'+cab+'</tbody></table></div>'



def gerar_relatorio(caminho, problema, ajuste, cfg, sol, registro, caminhos_csv, grade, curvas, pontos_experimentais):
    titulo = html.escape(" + ".join(s.nome for s in problema.substancias))
    corpo=[
        '<p class="eyebrow">Relatório de equilíbrio líquido–vapor</p>',
        f'<h1>Peng–Robinson · {titulo}</h1>',
        '<p class="sub">Ponto de bolha a %s K · relatório gerado em %s</p>' %
        (fmt(problema.T),datetime.now().astimezone().strftime("%d/%m/%Y às %H:%M")),
        secao_resumo(problema,ajuste,sol),
        secao_avisos(problema,ajuste,sol),
        secao_objetivo(),
        secao_equacoes(problema),
        secao_convergencia(sol,registro,grade,cfg),
        secao_fugacidades(problema,sol),
        secao_diagrama_pxy(problema,sol,curvas,registro,pontos_experimentais),
        secao_parametros(sol),
        '<h2>7. Dados de entrada e tolerâncias</h2>',secao_entrada(problema,ajuste,cfg),
        secao_arquivos(caminhos_csv,registro),
        '<div class="footer">Relatório gerado localmente pelo script Python. Não utiliza bibliotecas externas nem serviços online. '
        'Os resultados fora do ponto experimental são previsões do modelo e exigem validação independente.</div>',
    ]
    pagina=('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="description" content="Relatório didático de ELV com Peng-Robinson">'
            f'<title>ELV Peng-Robinson — {titulo}</title><style>{CSS}</style></head>'
            f'<body><main>{"".join(corpo)}</main></body></html>')
    with open(caminho,"w",encoding="utf-8") as arquivo:
        arquivo.write(pagina)
    return caminho
