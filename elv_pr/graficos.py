"""Gráficos SVG gerados diretamente com a biblioteca padrão."""
import html
import math
from .formatacao import fmt

def _ticks_log(y_min, y_max, max_ticks=7):
    lo, hi = math.floor(y_min), math.ceil(y_max)
    passo = max(1, int(math.ceil((hi - lo) / max_ticks)))
    return list(range(lo, hi + 1, passo))



def grafico_pressao_svg(pressao, tolerancia):
    """Erro |S-1| por iteração do loop de pressão, com eixo y logarítmico."""
    pontos = [(int(l["iter_P"]), float(l["erro_S_menos_1"])) for l in pressao
              if math.isfinite(float(l["erro_S_menos_1"])) and float(l["erro_S_menos_1"]) > 0]
    if not pontos:
        return '<p class="muted">Não há pontos positivos suficientes para desenhar a convergência.</p>'

    W, H, ml, mr, mt, mb = 820, 390, 82, 24, 48, 68
    pw, ph = W - ml - mr, H - mt - mb
    x0, x1 = min(x for x, _ in pontos), max(x for x, _ in pontos)
    if x0 == x1:
        x1 = x0 + 1
    logs = [math.log10(y) for _, y in pontos]
    if tolerancia > 0:
        logs.append(math.log10(tolerancia))
    y0, y1 = math.floor(min(logs)), math.ceil(max(logs))
    if y0 == y1:
        y0 -= 1
        y1 += 1
    px = lambda x: ml + (x - x0) / (x1 - x0) * pw
    py = lambda ly: mt + (y1 - ly) / (y1 - y0) * ph

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Erro absoluto S menos 1 por iteração, escala logarítmica">',
         f'<text class="small-title" x="{ml}" y="23">Convergência do loop de pressão</text>']
    for e in _ticks_log(y0, y1):
        y = py(e)
        s.append(f'<line class="grid" x1="{ml}" x2="{W-mr}" y1="{y:.1f}" y2="{y:.1f}"/>')
        s.append(f'<text x="{ml-10}" y="{y+4:.1f}" text-anchor="end">10^{e}</text>')
    xticks = list(range(x0, x1 + 1)) if x1 - x0 <= 8 else sorted(set([x0, round((x0+x1)/2), x1]))
    for x in xticks:
        xp = px(x)
        s.append(f'<line class="grid" x1="{xp:.1f}" x2="{xp:.1f}" y1="{mt}" y2="{mt+ph}"/>')
        s.append(f'<text x="{xp:.1f}" y="{mt+ph+19}" text-anchor="middle">{x}</text>')
    s.append(f'<path class="axis" d="M{ml},{mt} V{mt+ph} H{W-mr}"/>')
    if 10**y0 <= tolerancia <= 10**y1:
        yt = py(math.log10(tolerancia))
        s.append(f'<line class="threshold" x1="{ml}" x2="{W-mr}" y1="{yt:.1f}" y2="{yt:.1f}"/>')
        s.append(f'<text x="{W-mr-4}" y="{yt-6:.1f}" text-anchor="end">tolerância</text>')
    coords = " ".join(f'{px(x):.1f},{py(math.log10(y)):.1f}' for x, y in pontos)
    s.append(f'<polyline class="line-main" points="{coords}"/>')
    for x, y in pontos:
        s.append(f'<circle class="point-main" cx="{px(x):.1f}" cy="{py(math.log10(y)):.1f}" r="4"><title>iteração {x}: erro {y:.4e}</title></circle>')
    s.append(f'<text x="{ml+pw/2:.1f}" y="{H-17}" text-anchor="middle">Iteração do loop de pressão</text>')
    s.append(f'<text x="18" y="{mt+ph/2:.1f}" transform="rotate(-90 18 {mt+ph/2:.1f})" text-anchor="middle">|S − 1| (escala log)</text>')
    s.append('</svg>')
    return "".join(s)



def grafico_objetivo_svg(grade, avaliacoes, k12_otimo):
    """F(k12): linha da grade recalculada, pontos da seção áurea e solução final."""
    g = [(float(l["k12"]), float(l["F"])) for l in grade
         if math.isfinite(float(l["F"])) and float(l["F"]) >= 0]
    a = [(float(l["k12"]), float(l["F"])) for l in avaliacoes
         if math.isfinite(float(l["F"])) and float(l["F"]) >= 0]
    if not g:
        return '<p class="muted">A grade de F(k12) não foi calculada.</p>'

    W, H, ml, mr, mt, mb = 820, 390, 88, 28, 48, 68
    pw, ph = W - ml - mr, H - mt - mb
    xs = [x for x, _ in g] + [x for x, _ in a] + [k12_otimo]
    xmin, xmax = min(xs), max(xs)
    if xmin == xmax:
        xmax = xmin + 1
    positivos = [y for _, y in g + a if y > 0]
    piso = min(positivos) / 10 if positivos else 1e-16
    ys = [math.log10(max(y, piso)) for _, y in g + a]
    ymin, ymax = math.floor(min(ys)), math.ceil(max(ys))
    if ymin == ymax:
        ymin -= 1
        ymax += 1
    px = lambda x: ml + (x - xmin) / (xmax - xmin) * pw
    py = lambda ly: mt + (1 - (ly - ymin) / (ymax - ymin)) * ph

    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Função objetivo F em função do parâmetro k12">',
         f'<text class="small-title" x="{ml}" y="23">Função objetivo F em função de k₁₂</text>']
    for e in _ticks_log(ymin, ymax):
        y = py(e)
        s.append(f'<line class="grid" x1="{ml}" x2="{W-mr}" y1="{y:.1f}" y2="{y:.1f}"/>')
        s.append(f'<text x="{ml-10}" y="{y+4:.1f}" text-anchor="end">10^{e}</text>')
    for i in range(5):
        xval = xmin + (xmax - xmin) * i / 4
        xp = px(xval)
        s.append(f'<line class="grid" x1="{xp:.1f}" x2="{xp:.1f}" y1="{mt}" y2="{mt+ph}"/>')
        s.append(f'<text x="{xp:.1f}" y="{mt+ph+19}" text-anchor="middle">{xval:.4f}</text>')
    s.append(f'<path class="axis" d="M{ml},{mt} V{mt+ph} H{W-mr}"/>')
    line = " ".join(f'{px(x):.1f},{py(math.log10(max(y,piso))):.1f}' for x,y in g)
    s.append(f'<polyline class="line-grid" points="{line}"/>')
    for x, y in g:
        s.append(f'<circle class="point-main" cx="{px(x):.1f}" cy="{py(math.log10(max(y,piso))):.1f}" r="2.5"><title>grade: k12={x:.7g}; F={y:.7g}</title></circle>')
    for x, y in a:
        s.append(f'<rect class="point-search" x="{px(x)-4:.1f}" y="{py(math.log10(max(y,piso)))-4:.1f}" width="8" height="8"><title>seção áurea: k12={x:.7g}; F={y:.7g}</title></rect>')
    f_best = min((y for x,y in g+a if abs(x-k12_otimo) < 1e-10), default=None)
    if f_best is not None:
        xb, yb = px(k12_otimo), py(math.log10(max(f_best,piso)))
        s.append(f'<path class="point-best" d="M{xb:.1f},{yb-7:.1f} L{xb+7:.1f},{yb:.1f} L{xb:.1f},{yb+7:.1f} L{xb-7:.1f},{yb:.1f} Z"><title>k12 final={k12_otimo:.8g}; F={f_best:.8g}</title></path>')
    else:
        xb = px(k12_otimo)
        s.append(f'<line class="threshold" x1="{xb:.1f}" x2="{xb:.1f}" y1="{mt}" y2="{mt+ph}"/>')
    s.append(f'<text x="{ml+pw/2:.1f}" y="{H-17}" text-anchor="middle">Parâmetro de interação k₁₂</text>')
    s.append(f'<text x="18" y="{mt+ph/2:.1f}" transform="rotate(-90 18 {mt+ph/2:.1f})" text-anchor="middle">F (escala log)</text>')
    s.append('</svg>')
    return "".join(s)



def grafico_fugacidades_svg(problema, sol):
    """Barras horizontais pareadas; cada componente tem escala própria para comparar L e V."""
    n = len(sol.f_liquido)
    W, H = 1000, 130 + n * 135
    ml, mr, mt = 220, 210, 48
    pw = W - ml - mr
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Barras comparando fugacidades líquida e vapor por componente">',
         f'<text class="small-title" x="{ml}" y="24">Comparação de fᴸ e fⱽ (atm; escala própria por componente)</text>']
    for i, sub in enumerate(problema.substancias):
        fl, fv = sol.f_liquido[i], sol.f_vapor[i]
        vmax = max(fl, fv, 1e-15) * 1.10
        px = lambda v: ml + v / vmax * pw
        top = mt + 20 + i * 135
        s.append(f'<text class="small-title" x="18" y="{top+22}">{html.escape(sub.nome)} ({html.escape(sub.formula)})</text>')
        for j in range(3):
            v = vmax * j / 2
            x = px(v)
            s.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{top+2}" y2="{top+91}"/>')
            s.append(f'<text x="{x:.1f}" y="{top+110}" text-anchor="middle">{v:.4g}</text>')
        yl, yv = top + 13, top + 53
        s.append(f'<text x="{ml-12}" y="{yl+13}" text-anchor="end">Líquido</text>')
        s.append(f'<text x="{ml-12}" y="{yv+13}" text-anchor="end">Vapor</text>')
        s.append(f'<rect class="bar-l" x="{ml}" y="{yl}" width="{max(0,px(fl)-ml):.2f}" height="19" rx="3"><title>fL={fl:.12g} atm</title></rect>')
        s.append(f'<rect class="bar-v" x="{ml}" y="{yv}" width="{max(0,px(fv)-ml):.2f}" height="19" rx="3"><title>fV={fv:.12g} atm</title></rect>')
        s.append(f'<text x="{ml+pw+15}" y="{yl+14}">fᴸ = {fl:.10g} atm</text>')
        s.append(f'<text x="{ml+pw+15}" y="{yv+14}">fⱽ = {fv:.10g} atm</text>')
    s.append('</svg>')
    return "".join(s)



def _sobrescrito(n):
    """-5 -> '⁻⁵' (rótulos do eixo logarítmico)."""
    return str(n).translate(str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))



def _ticks_lineares(vmin, vmax, alvo=6):
    """Marcações redondas (1, 2, 5 × 10ⁿ) entre vmin e vmax."""
    if vmax <= vmin:
        return [vmin]
    bruto = (vmax - vmin) / alvo
    pot = 10.0 ** math.floor(math.log10(bruto))
    passo = next(m * pot for m in (1, 2, 5, 10) if m * pot >= bruto)
    inicio = math.ceil(vmin / passo - 1e-9) * passo
    n = int(math.floor((vmax - inicio) / passo + 1e-9)) + 1
    return [inicio + k * passo for k in range(n)]



def grafico_pxy_svg(pontos, problema, escala, pontos_experimentais):
    validos = [p for p in pontos if p is not None]
    if not validos:
        return '<p>Nenhum ponto do diagrama convergiu.</p>'
    ps = [p["P_atm"] for p in validos] + [p[2] for p in pontos_experimentais]
    W,H,ml,mr,mt,mb = 900,480,86,26,44,64
    pw,ph = W-ml-mr,H-mt-mb
    px = lambda x: ml+x*pw
    if escala == "log":
        lo,hi = math.floor(math.log10(min(ps))), math.ceil(math.log10(max(ps)))
        if lo == hi: hi += 1
        py = lambda p: mt+(hi-math.log10(p))/(hi-lo)*ph
        ticks = [(py(10**e), "10"+_sobrescrito(e)) for e in _ticks_log(lo,hi)]
    else:
        marcas = _ticks_lineares(0, max(ps), 7)
        top = max(max(ps)*1.03, marcas[-1])
        py = lambda p: mt+(1-p/top)*ph
        ticks = [(py(v),fmt(v,4)) for v in marcas]
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Diagrama P x y, escala {escala}">',
         f'<text class="small-title" x="{ml}" y="23">Bolha e orvalho a {fmt(problema.T)} K — escala {escala}</text>']
    for yy, label in ticks:
        s.append(f'<line class="grid" x1="{ml}" x2="{W-mr}" y1="{yy:.1f}" y2="{yy:.1f}"/><text x="{ml-10}" y="{yy+4:.1f}" text-anchor="end">{label}</text>')
    for i in range(6):
        xx=px(i/5)
        s.append(f'<line class="grid" x1="{xx:.1f}" x2="{xx:.1f}" y1="{mt}" y2="{mt+ph}"/><text x="{xx:.1f}" y="{mt+ph+19}" text-anchor="middle">{i/5:.1f}</text>')
    s.append(f'<path class="axis" d="M{ml},{mt} V{mt+ph} H{W-mr}"/>')
    for chave, cor in (("x1", "#137a85"), ("y1", "#d47435")):
        segmento=[]
        for ponto in pontos+[None]:
            if ponto is None:
                if segmento:
                    s.append(f'<polyline fill="none" stroke="{cor}" stroke-width="3" points="{chr(32).join(segmento)}"/>')
                    segmento=[]
            else:
                segmento.append(f'{px(ponto[chave]):.1f},{py(ponto["P_atm"]):.1f}')
    for i,(x,y,P) in enumerate(pontos_experimentais,1):
        for frac,cor,nome in ((x,"#137a85","líquido"),(y,"#d47435","vapor")):
            s.append(f'<circle cx="{px(frac):.1f}" cy="{py(P):.1f}" r="5" fill="white" stroke="{cor}" stroke-width="2"><title>Experimental {i}, {nome}: fração={frac:.5g}; P={P:.5g} atm</title></circle>')
    s.append(f'<text x="{ml+pw/2}" y="{H-17}" text-anchor="middle">Fração molar do componente 1: x₁ ou y₁</text>')
    s.append(f'<text x="18" y="{mt+ph/2}" transform="rotate(-90 18 {mt+ph/2})" text-anchor="middle">Pressão [atm]</text></svg>')
    return "".join(s)
