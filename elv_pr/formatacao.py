"""Formatação de números e tabelas HTML."""
import html
import math

def fmt(valor, digitos=6):
    if isinstance(valor, bool):
        return "sim" if valor else "não"
    if isinstance(valor, float):
        if math.isnan(valor):
            return "não disponível"
        if math.isinf(valor):
            return "∞" if valor > 0 else "−∞"
        return "%.*g" % (digitos, valor)
    return html.escape(str(valor))



def tabela(linhas, colunas, cabecalhos=None, digitos=6):
    cabecalhos = cabecalhos or colunas
    topo = "".join("<th>%s</th>" % c for c in cabecalhos)
    corpo = "".join("<tr>" + "".join("<td>%s</td>" % fmt(linha.get(c, ""), digitos)
                                      for c in colunas) + "</tr>" for linha in linhas)
    return '<div class="table-scroll"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (topo, corpo)



def tabela_pares(pares, digitos=7):
    corpo = "".join('<tr><td>%s</td><td>%s</td></tr>' % (html.escape(str(n)), fmt(v, digitos))
                    for n, v in pares)
    return '<div class="table-scroll"><table><tbody>%s</tbody></table></div>' % corpo



def cartao(rotulo, valor, detalhe=""):
    return ('<div class="card"><div class="card-label">%s</div><div class="card-value">%s</div>'
            '<div class="card-detail">%s</div></div>' % (rotulo, valor, detalhe))



def aviso(texto, tipo=""):
    return '<div class="note %s">%s</div>' % (tipo, texto)
