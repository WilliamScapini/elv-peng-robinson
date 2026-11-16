# ELV Peng-Robinson em Python

Cálculo de pressão de bolha e composição de vapor em misturas binárias pela
equação de Peng–Robinson, com ajuste de um único parâmetro de interação `k12`
aos pontos de uma isoterma. O exemplo principal reproduz as tabelas do artigo
de etanol–água a 200 °C. Há também um exemplo metano–etano com os dados do
script de origem `elv_peng_robinson_pxy.py`.

Requer **Python 3.9 ou posterior**. O programa funciona offline e usa somente
a biblioteca padrão. Não é necessário instalar pacotes com `pip`.

## Executar

Baixe o repositório em **Code → Download ZIP**, extraia a pasta e abra um
terminal dentro dela. Execute:

```bash
python main.py
```

No Linux/macOS, pode ser necessário usar `python3`; no Windows, `py`.
O programa abre automaticamente o **relatório resumido** no navegador.
Se o navegador não abrir, abra `resultados/etanol_agua_200C/relatorio.html`
com um duplo clique. O relatório apresenta os desvios médios, os diagramas
dos dois cenários e a tabela comparativa para consulta durante a leitura do artigo.
Os links levam aos CSVs e aos diagnósticos completos.

Outras opções:

```bash
python main.py --sem-navegador
python main.py dados/metano_etano.json
python main.py dados/etanol_agua_200C.json --saida resultados/minha_execucao
python main.py dados/etanol_agua_200C.json --validar
python main.py --versao
python main.py --help
```

O caminho de uma entrada informada e o argumento `--saida` são relativos ao
terminal. A pasta `saida.pasta` do JSON é relativa à raiz deste projeto.
O comando padrão funciona também se `main.py` for chamado pelo caminho completo.
Uma nova execução na mesma pasta substitui as saídas de mesmo nome. Para
preservar uma execução usada no artigo, guarde a pasta ou use outra `--saida`.

## Inserir substâncias e dados experimentais

Faça uma cópia de `dados/etanol_agua_200C.json` e edite-a em um editor de texto.
Mude os dois componentes, a temperatura, a fonte dos dados e a lista de pontos.
As frações `x1` e `y1` sempre se referem ao **primeiro** componente. As frações
do segundo são calculadas como `1 - x1` e `1 - y1`.

```json
"pontos_experimentais": [
  {"x1": 0.023, "y1": 0.134, "P_atm": 17.692},
  {"x1": 0.048, "y1": 0.219, "P_atm": 19.597}
]
```

Esse trecho é parte do arquivo completo, não um arquivo de entrada isolado.
Use **ponto decimal** e `true`/`false` sem aspas. JSON não aceita comentários
nem vírgula após o último item. Cada arquivo representa uma temperatura;
separe dados de isotermas diferentes em arquivos distintos.

| Campo | Significado e unidade |
| --- | --- |
| `substancias` | Exatamente dois componentes, na ordem 1 e 2 |
| `Tc_K`, `Pc_atm`, `omega` | Temperatura crítica em K, pressão crítica em atm e fator acêntrico |
| `condicoes.T_K` | Temperatura da isoterma em K; 200 °C = 473,15 K |
| `condicoes.R_atm_L_mol_K` | Constante dos gases em L atm mol⁻¹ K⁻¹ |
| `condicoes.correlacao_m` | `peng_robinson` (original) ou `planilha` (expressão do script de origem) |
| `pontos_experimentais` | `x1` líquido, `y1` vapor e `P_atm`; todos na mesma temperatura |
| `ajuste_k12.ajustar` | `true` ajusta; `false` usa `k12_fixo` |
| `ajuste_k12.k12_min`, `k12_max` | Intervalo da seção áurea |
| `comparar_k12_zero` | Incluir cenário de referência com `k12 = 0` |
| `diagrama_pxy.gerar`, `n_pontos` | Gerar diagrama e número de composições na grade, incluindo puros |
| `numerica` | Tolerâncias e máximos de iterações; detalhes em `docs/METODO.md` |
| `numerica.n_pontos_grade_f` | Grade adicional de F; `0` desativa; mínimo ativo: `3` |
| `historico_detalhado_busca` | `true` registra todos os loops da busca; pode gerar CSVs grandes |
| `saida.csv_separador`, `csv_decimal` | Para Excel em português, use `";"` e `","`, respectivamente |
| `fonte_dados` | Origem efetiva dos dados e propriedades, para manter a atribuição |

Os pontos do ajuste devem satisfazer `0 < x1 < 1`, `0 ≤ y1 ≤ 1` e `P_atm > 0`.
Os extremos puros são calculados no diagrama e ficam fora do ajuste.
Chaves desconhecidas, dados não finitos e unidades implícitas não são convertidos
automaticamente: forneça os valores nas unidades indicadas nos nomes dos campos.

## Resultados

Na pasta de saída:

| Arquivo | Conteúdo |
| --- | --- |
| `relatorio.html` | Consulta resumida dos cenários e tabela comparativa |
| `tabela_1.csv` | Pressões e frações experimentais e calculadas de cada cenário |
| `resumo.json` | `k12`, F, desvios médios, convergência e falhas do diagrama |
| `entrada_utilizada.json` | Cópia exata da entrada desta execução |
| `metadados.json` | Versão, hashes SHA-256, ambiente, entrada, resultados e commit quando disponível |
| `zero/`, `ajustado/` ou `fixo/` | Relatórios completos e históricos por cenário |

Dentro de cada cenário, os CSVs registram a busca (`loop_k12.csv`), as
iterações finais de pressão e composição (`loop_pressao.csv`, `loop_y.csv`),
as raízes de Cardano (`raizes_cardano.csv`), os pontos comparados
(`pontos_experimentais.csv`) e, quando habilitados, a grade de F e o diagrama.
No histórico de ajuste, `dP_pct` e `dy1_pct` descrevem o **primeiro ponto**;
`desvio_medio_P_pct` e `desvio_medio_y1` descrevem **todos os pontos**.
O histórico padrão guarda os loops detalhados da avaliação final; ative
`historico_detalhado_busca` para auditar também cada tentativa intermediária.

Para o exemplo do artigo, os resultados esperados são:

| Cenário | k₁₂ | F | Desvio médio absoluto de P | Desvio médio absoluto de y₁ |
| --- | --- | --- | --- | --- |
| Sem ajuste | 0 | 933,50884 | 24,141% | 0,09423 |
| Ajustado | −0,08367651 | 10,08031 | 2,340% | 0,01670 |

F é adimensional. O erro de P é relativo e expresso em porcentagem; o de y₁
é absoluto e expresso em fração molar nessa tabela. Nos termos de F, o erro
de y₁ é multiplicado por 100 (pontos percentuais).

## Organização do código

```text
main.py                 entrada para execução
elv_pr/
  configuracao.py       leitura e validação do JSON
  modelos.py            estruturas do problema e das configurações
  cardano.py            solução da equação cúbica
  eos.py                parâmetros PR, mistura, raízes e fugacidades
  equilibrio.py         iterações de y e de pressão
  ajuste.py             função objetivo e seção áurea de k12
  diagrama.py           curvas P–x–y
  registro.py           históricos e exportação CSV
  formatacao.py         números e tabelas HTML
  graficos.py           gráficos SVG locais
  estilos.py            apresentação do HTML
  relatorio.py          diagnóstico completo por cenário
  proveniencia.py       hashes, versão e ambiente
  cli.py                execução e relatório resumido
dados/                  exemplos editáveis em JSON
tests/                  verificações com unittest, da biblioteca padrão
docs/                   método, citação e publicação
```

## Verificar os cálculos

```bash
python -S -m unittest discover -s tests -v
```

`-S` desativa a carga de pacotes de terceiros. Os testes verificam as tabelas
do artigo, raízes conhecidas, igualdade de fugacidades, falhas de convergência,
validação das entradas e independência entre configurações.

## Citação e publicação

Consulte [docs/CITACAO.md](docs/CITACAO.md) para os textos de Materiais e métodos
e referências, e [docs/PUBLICACAO.md](docs/PUBLICACAO.md) para publicar esta
pasta como repositório independente. A versão citada é **1.0.0**, disponível na
[release v1.0.0](https://github.com/WilliamScapini/elv-peng-robinson/releases/tag/v1.0.0).
O arquivo `CITATION.cff` registra o autor, a versão e os endereços de publicação.
Não há DOI atribuído.

O código e a documentação estão sob licença MIT. A licença não altera os
direitos sobre os dados experimentais de terceiros. Os dados de etanol–água
foram transcritos do artigo fornecido, que os atribui a Barr-David e Dodge
(1959), conforme a ficha da atividade. O documento completo e as figuras do
artigo não são distribuídos nesta pasta.
