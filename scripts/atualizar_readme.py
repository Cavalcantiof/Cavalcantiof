"""
Robô do laboratório: atualiza a seção automática do README.

Roda todo dia pelo GitHub Actions. Consulta a API pública do GitHub,
monta o "Diário do laboratório" e substitui o texto entre os marcadores
<!--LAB:START--> e <!--LAB:END--> no README.md.

Só usa a biblioteca padrão do Python (nada de pip install).
"""

import json
import os
import random
import re
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

USUARIO = "Cavalcantiof"
INICIO_PYTHON = date(2026, 7, 1)          # quando comecei o foco em Python
FUSO_LOCAL = timezone(timedelta(hours=-3))  # horário de Recife/Olinda
README = Path(__file__).resolve().parent.parent / "README.md"

FRASES = [
    "Se dá pra fazer 3 vezes, dá pra automatizar.",
    "Planilha manual é só um script que ainda não nasceu.",
    "Conferir é importante. Conferir automaticamente é melhor.",
    "O melhor clique é aquele que ninguém precisa dar.",
    "Primeiro faz funcionar, depois faz bonito, depois faz sozinho.",
    "Todo processo repetitivo é um bug esperando correção.",
]


def chamar_api(caminho: str):
    """Faz um GET na API do GitHub e devolve o JSON já convertido."""
    req = urllib.request.Request(
        f"https://api.github.com{caminho}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USUARIO},
    )
    token = os.getenv("GITHUB_TOKEN")
    if token:  # com token o limite de requisições é bem maior
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=20) as resposta:
        return json.load(resposta)


def montar_diario() -> str:
    agora = datetime.now(FUSO_LOCAL)
    repos = chamar_api(f"/users/{USUARIO}/repos?sort=pushed&per_page=100")
    # ignora forks e o próprio repositório do perfil
    meus = [r for r in repos if not r["fork"] and r["name"] != USUARIO]

    dias_python = (agora.date() - INICIO_PYTHON).days
    # semente = data de hoje -> a frase muda uma vez por dia, não a cada execução
    frase = random.Random(agora.date().toordinal()).choice(FRASES)

    linhas = [
        "🧪 DIÁRIO DO LABORATÓRIO",
        f"├── 🕒 última execução do robô: {agora:%d/%m/%Y às %H:%M} (Recife)",
        f"├── 🐍 dias estudando Python: {dias_python}",
        f"├── 📦 projetos públicos: {len(meus)}",
        "├── 🔧 mexi recentemente em:",
    ]
    if meus:
        recentes = meus[:3]
        for i, repo in enumerate(recentes):
            ramo = "└──" if i == len(recentes) - 1 else "├──"
            linguagem = repo["language"] or "—"
            linhas.append(f"│   {ramo} {repo['name']} ({linguagem}) · {repo['pushed_at'][:10]}")
    else:
        linhas.append("│   └── (nenhum projeto público ainda)")
    linhas.append(f"└── 💬 frase do dia: \"{frase}\"")

    return "```text\n" + "\n".join(linhas) + "\n```"


def main():
    conteudo = README.read_text(encoding="utf-8")
    novo_bloco = f"<!--LAB:START-->\n{montar_diario()}\n<!--LAB:END-->"
    atualizado = re.sub(
        r"<!--LAB:START-->.*?<!--LAB:END-->", novo_bloco, conteudo, flags=re.DOTALL
    )
    if atualizado == conteudo:
        print("Nada mudou no README.")
        return
    README.write_text(atualizado, encoding="utf-8")
    print("README atualizado com sucesso.")


if __name__ == "__main__":
    main()
