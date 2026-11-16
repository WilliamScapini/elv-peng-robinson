# Método numérico e reprodução do artigo

O programa foi modularizado a partir de `elv_peng_robinson_pxy.py`. As
expressões de Cardano, de Peng–Robinson, as regras de mistura e as atualizações
iterativas foram preservadas. As entradas deixaram de ser variáveis globais
e passaram a ser argumentos explícitos, carregados de JSON. Isso permite
executar sistemas diferentes na mesma sessão sem trocar dados entre cálculos.

## Unidades e equação de estado

O programa usa K, atm, L e mol, com `R` consistente com essas unidades.
Para cada componente:

```text
Tr = T/Tc
alpha = [1 + m(1 - sqrt(Tr))]^2
a = 0.45724 R^2 Tc^2 alpha/Pc
b = 0.07780 R Tc/Pc
```

Em `peng_robinson`, `m = 0.37464 + 1.54226 omega - 0.26992 omega^2`.
Em `planilha`, `m = 0.48 + 1.574 omega - 0.176 omega^2`; esta segunda
expressão preserva a configuração do script original e não é a correlação
original de Peng–Robinson. O exemplo do artigo usa `peng_robinson`.

A mistura usa `a_ij = (1 - k_ij) sqrt(a_i a_j)`, `a = soma(z_i z_j a_ij)`
e `b = soma(z_i b_i)`, com `k11 = k22 = 0` e `k12 = k21`.
Resolve-se a cúbica de PR em Z por Cardano. Entre as raízes reais com
`Z > B`, seleciona-se a menor para o líquido e a maior para o vapor,
cada fase na respectiva composição. Os coeficientes de fugacidade seguem
a expressão registrada em `eos.termos_fugacidade`.

## Loops de equilíbrio e ajuste

Para cada ponto experimental, os chutes são sua pressão e sua composição
de vapor medidas. A pressão fica fixa no loop interno:

```text
K_i = phi_i_liquido / phi_i_vapor
S = soma(x_i K_i)
y_i_novo = x_i K_i / S
```

O loop interno para quando a maior variação de y fica abaixo de `tol_y`.
O loop intermediário atualiza `P_novo = P S` e para quando
`abs(S - 1) < tol_pressao` e o loop interno também convergiu.
Uma solução com `Z_vapor - Z_liquido < 1e-6` é rejeitada para evitar a
solução trivial de fases iguais. Esse critério não constitui uma análise
global de estabilidade de fases.

O loop externo usa seção áurea em `[k12_min, k12_max]` e minimiza:

```text
r_P = 100 (P_calc - P_exp)/P_exp
r_y = 100 (y1_calc - y1_exp)
F = media(r_P^2 + r_y^2)
```

Usar os valores absolutos antes de elevar ao quadrado, como faz a
implementação, produz a mesma F. Todos os pontos têm o mesmo peso.
Uma tentativa com falha recebe `F = inf` no histórico CSV e não é aceita
como solução. Não se ajusta apenas um subconjunto dos pontos válidos.
A busca não garante um mínimo global em uma função com múltiplos vales.
A grade adicional de F é um diagnóstico independente, sem alterar a busca.

| Configuração do artigo | Valor |
| --- | --- |
| `T_K`, `R_atm_L_mol_K` | 473,15; 0,08205 |
| Etanol: `Tc_K`, `Pc_atm`, `omega` | 514,00; 60,567; 0,64356 |
| Água: `Tc_K`, `Pc_atm`, `omega` | 647,13; 217,66; 0,34486 |
| `tol_y`, `max_iter_y` | 10⁻¹⁴; 200 |
| `tol_pressao`, `max_iter_pressao` | 10⁻¹²; 150 |
| `tol_k12`, `max_aval_k12` | 10⁻⁸; 100 |
| `k12_min`, `k12_max` | −0,5; 0,5 |
| `n_pontos_grade_f` | 101 |
| `diagrama_pxy.n_pontos` | 61, além das composições experimentais |

O resultado ajustado é `k12 = -0.08367650873396874` e
`F = 10.08030978880905`, com 42 avaliações. Pequenas diferenças nos últimos
dígitos podem ocorrer entre plataformas. Os testes usam tolerâncias
compatíveis com os algarismos publicados, sem exigir identidade binária.

## Diagrama e componentes puros

Cada solução `(x1, P, y1)` fornece um ponto de bolha `(x1, P)` e um ponto
de orvalho `(y1, P)`. O diagrama utiliza continuação a partir do ponto
anterior e, se necessário, um chute pela correlação de Wilson. Nos extremos
puros, o mesmo procedimento impõe a igualdade das fugacidades das raízes
líquida e vapor da substância pura. Os puros ficam fora do ajuste. A 200 °C,
as pressões calculadas arredondam para 15,371 atm (água) e 29,022 atm (etanol).
Pontos que falham aparecem como lacunas e ficam identificados no CSV.

O cálculo é binário, isotérmico e com um k12 constante. Não inclui análise
global de estabilidade, equilíbrio líquido–líquido nem procura dedicada de
azeótropo. A coincidência das curvas nos extremos puros não identifica um
azeótropo interno. A reprodução das tabelas verifica a implementação e a
correlação apresentada; não valida previsões em outras condições.

## Rastreabilidade

O programa copia os bytes da entrada, registra a configuração e calcula
SHA-256 de cada módulo, `main.py`, `VERSION` e `CITATION.cff`. O manifesto
ordenado desses hashes gera `codigo_sha256`. Também registra versão do
Python, plataforma, instante UTC, commit e alterações locais quando o Git
está disponível, além de hashes dos arquivos de saída desta execução.

O relatório resumido arredonda os números para leitura. Para recalcular ou
comparar com mais algarismos, use os CSVs e `resumo.json`. O relatório
completo de cada cenário preserva os gráficos e a explicação do script de
origem. Os históricos detalhados não entram no HTML resumido.
