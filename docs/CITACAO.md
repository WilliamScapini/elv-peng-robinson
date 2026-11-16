# Citar a implementação no artigo

O software **ELV Peng-Robinson em Python**, de William José Scapini Prudencio,
está identificado pela versão **1.0.0**, tag `v1.0.0`.

Repositório: https://github.com/WilliamScapini/elv-peng-robinson

Versão citada: https://github.com/WilliamScapini/elv-peng-robinson/releases/tag/v1.0.0

## Materiais e métodos

> O algoritmo foi implementado em Python, utilizando exclusivamente a biblioteca
> padrão. O código correspondente à versão 1.0.0 utilizada nos cálculos está
> disponível no repositório de Prudencio (2026). Os dados de entrada da isoterma
> de 200 °C estão no arquivo `dados/etanol_agua_200C.json` dessa versão.

## Referência do software

> PRUDENCIO, William José Scapini. *ELV Peng-Robinson em Python*. Versão 1.0.0.
> GitHub, 2026. Disponível em:
> https://github.com/WilliamScapini/elv-peng-robinson/releases/tag/v1.0.0.
> Acesso em: 16 nov. 2026.

A referência identifica a release usada na reprodução das tabelas.
O arquivo `metadados.json` dos resultados registra adicionalmente o commit,
a configuração e os hashes dos arquivos executados. Preserve a tag citada;
para mudanças posteriores, publique uma nova versão. A data de acesso deve
corresponder à consulta efetiva quando a referência for reutilizada.

## Dados experimentais e modelo

O repositório documenta o procedimento de cálculo. Mantenha a atribuição dos
dados experimentais a Barr-David e Dodge, como no artigo:

> BARR-DAVID, F.; DODGE, B. F. Vapor-liquid equilibrium at high pressures: the
> systems ethanol-water and 2-propanol-water. *Journal of Chemical & Engineering
> Data*, v. 4, n. 2, p. 107–121, 1959. DOI: 10.1021/je60002a003.

Para a equação de estado:

> PENG, D.-Y.; ROBINSON, D. B. A new two-constant equation of state.
> *Industrial & Engineering Chemistry Fundamentals*, v. 15, n. 1,
> p. 59–64, 1976. DOI: 10.1021/i160057a011.

O arquivo `CITATION.cff` permite ao GitHub oferecer a opção de citar o
software. Mantenha o título, o autor e a versão coerentes entre esse arquivo,
`VERSION`, `elv_pr/__init__.py`, a tag e o artigo. Veja a
[documentação oficial do GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files).
