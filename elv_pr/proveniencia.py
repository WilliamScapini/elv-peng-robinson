"""Identificação da implementação e do ambiente usados em cada execução."""
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__


def hash_arquivo(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def identificar_codigo(raiz):
    """O hash independe da existência do Git e da pasta de instalação."""
    arquivos = [raiz / "main.py", raiz / "VERSION", raiz / "CITATION.cff"]
    arquivos += sorted((raiz / "elv_pr").glob("*.py"))
    hashes = {p.relative_to(raiz).as_posix(): hash_arquivo(p) for p in arquivos}
    manifesto = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    git = {"commit": None, "alteracoes_locais": None}
    try:
        def comando(*argumentos):
            return subprocess.check_output(
                ["git", "-C", str(raiz), *argumentos], stderr=subprocess.DEVNULL,
                text=True, timeout=5,
            ).strip()
        if Path(comando("rev-parse", "--show-toplevel")).resolve() == raiz.resolve():
            git = {"commit": comando("rev-parse", "HEAD"),
                   "alteracoes_locais": bool(comando("status", "--porcelain"))}
    except (OSError, subprocess.SubprocessError):
        pass
    return {"versao": __version__, "codigo_sha256": hashlib.sha256(manifesto).hexdigest(),
            "arquivos_sha256": hashes, "git": git}


def metadados(raiz, configuracao):
    return {
        "software": "ELV Peng-Robinson em Python", **identificar_codigo(raiz),
        "inicio_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "plataforma": platform.platform(),
        "entrada_sha256": hashlib.sha256(configuracao.conteudo_original).hexdigest(),
        "entrada": configuracao.dados,
        "observacao": "Resultados de correlação; dados experimentais conforme a fonte registrada na entrada.",
    }


def salvar_json(caminho, dados):
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")
