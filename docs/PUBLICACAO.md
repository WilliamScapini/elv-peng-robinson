# Publicação com GitHub CLI

Repositório público: https://github.com/WilliamScapini/elv-peng-robinson

Release citada: https://github.com/WilliamScapini/elv-peng-robinson/releases/tag/v1.0.0

O comando do GitHub CLI é `gh`. A publicação inicial utiliza esta sequência,
executada dentro desta pasta, depois de conferir `gh auth status`:

```bash
git init -b main
git add .
git commit -m "Publica implementação modular do ELV com Peng-Robinson"
gh repo create WilliamScapini/elv-peng-robinson --public --source=. --remote=origin --push
git tag -a v1.0.0 -m "Versão usada nos cálculos do artigo"
git push origin v1.0.0
gh release create v1.0.0 --verify-tag --title "ELV Peng-Robinson em Python 1.0.0" --notes "Implementação e entradas para reprodução dos cálculos do artigo."
```

Essa sequência é um registro da publicação inicial; não deve ser repetida
em um repositório que já existe. Se o Git ainda não tiver identidade local,
configure `git config user.name` e `git config user.email` antes do commit.
A autenticação do Git via CLI pode ser configurada com `gh auth setup-git`.

Para consultar a publicação e o commit:

```bash
gh repo view WilliamScapini/elv-peng-robinson --web
gh release view v1.0.0 --repo WilliamScapini/elv-peng-robinson
git rev-parse HEAD
```

Para obter a versão citada em outra máquina:

```bash
gh repo clone WilliamScapini/elv-peng-robinson
cd elv-peng-robinson
git checkout v1.0.0
python3 -S -m unittest discover -s tests -v
python3 main.py
```

Os resultados são ignorados no Git. A execução registra o commit quando
há uma pasta `.git`, e registra versão e hashes mesmo em um ZIP sem Git.
Mantenha a tag citada. Atualizações futuras devem receber outra versão,
com atualização de `VERSION`, `elv_pr/__init__.py` e `CITATION.cff`.

Referências dos comandos:
[gh repo create](https://cli.github.com/manual/gh_repo_create) e
[gh release create](https://cli.github.com/manual/gh_release_create).
