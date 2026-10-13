#!/usr/bin/env python3
"""
Detecta notas de concepto vacías o a medias en la carpeta de un tema (o en toda la sesión).

Uso: python3 -I revisar_notas.py <carpeta_tema_o_sesión> [--min-palabras 80]

Una nota de concepto (frontmatter `tipo: concepto`) está INCOMPLETA si:
- tiene menos de --min-palabras palabras de contenido (sin contar títulos, frontmatter,
  "## Mis notas" ni "## Contraste");
- no tiene el callout "En una frase" ([!abstract]) con texto;
- no tiene "## Qué es" con al menos 25 palabras;
- "## Fuentes" no cita ninguna página ("p. N");
- tiene secciones vacías (un título seguido de otro título o del final);
- quedan textos de la plantilla o marcadores de relleno (<...>, TODO, "por completar"…).

Sale con código 1 si hay alguna incompleta.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import re
import sys
from pathlib import Path

RELLENO = re.compile(r"<[a-záéíóúñ][^<>\n]{3,}>|\bTODO\b|\bTBD\b|por completar|pendiente de (?:rellenar|completar)|"
                     r"\(completar\)|lorem ipsum|\[\[A\]\]|\[\[C\]\]", re.I)
EXCLUIDAS = {"mis notas", "contraste"}


def secciones(cuerpo: str) -> list[tuple[str, str]]:
    """[(título en minúsculas, texto)] de las secciones ## del cuerpo; la primera es lo de antes del primer ##."""
    partes = re.split(r"^##\s+(.+?)\s*$", cuerpo, flags=re.M)
    resultado = [("", partes[0])]
    for i in range(1, len(partes), 2):
        resultado.append((partes[i].strip().lower(), partes[i + 1]))
    return resultado


def palabras(texto: str) -> int:
    texto = re.sub(r"^#.*$", "", texto, flags=re.M)
    texto = re.sub(r"^>\s*\[![^\]]+\][+-]?", "", texto, flags=re.M)
    return len(re.findall(r"[\wáéíóúüñÁÉÍÓÚÜÑ$\\]+", texto))


def revisar(p: Path, minimo: int) -> list[str]:
    texto = p.read_text(encoding="utf-8")
    if not texto.startswith("---"):
        return []
    partes = texto.split("---", 2)
    if len(partes) < 3 or not re.search(r"^tipo:\s*concepto\s*$", partes[1], re.M):
        return []
    cuerpo = partes[2]
    problemas = []

    secs = secciones(cuerpo)
    contenido = "".join(t for titulo, t in secs if titulo not in EXCLUIDAS)
    n = palabras(contenido)
    if n < minimo:
        problemas.append(f"solo {n} palabras de contenido (mínimo {minimo})")

    abstract = re.search(r"^>\s*\[!abstract\][^\n]*\n((?:>.*\n?)*)", cuerpo, re.M | re.I)
    if not abstract or palabras(re.sub(r"^>\s?", "", abstract.group(1), flags=re.M)) < 5:
        problemas.append('falta "En una frase" ([!abstract]) con contenido')

    por_titulo = {t: x for t, x in secs}
    que_es = next((x for t, x in secs if t.startswith("qué es") or t.startswith("que es")), None)
    if que_es is None or palabras(que_es) < 25:
        problemas.append('falta "## Qué es" o tiene menos de 25 palabras')

    fuentes = por_titulo.get("fuentes")
    if fuentes is None or not re.search(r"\bp(?:ág|ag)?s?\.\s*\d", fuentes):
        problemas.append('"## Fuentes" no cita ninguna página (p. N)')

    vacias = [t for t, x in secs[1:] if t not in EXCLUIDAS and not x.strip()]
    if vacias:
        problemas.append("secciones vacías: " + ", ".join(vacias))

    relleno = sorted({m.group(0) for m in RELLENO.finditer(cuerpo)})
    if relleno:
        problemas.append("texto de relleno o de la plantilla: " + ", ".join(relleno[:5]))
    return problemas


def main():
    args = sys.argv[1:]
    minimo = 80
    if "--min-palabras" in args:
        i = args.index("--min-palabras")
        minimo = int(args[i + 1])
        del args[i:i + 2]
    if not args:
        sys.exit(__doc__)
    raiz = Path(args[0]).expanduser().resolve()
    malas = 0
    for p in sorted(raiz.rglob("*.md")):
        if any(parte.startswith(".") for parte in p.relative_to(raiz).parts):
            continue
        problemas = revisar(p, minimo)
        if problemas:
            malas += 1
            print(f"✗ {p.relative_to(raiz)}")
            for prob in problemas:
                print(f"    - {prob}")
    print(f"Notas de concepto incompletas: {malas}")
    sys.exit(1 if malas else 0)


if __name__ == "__main__":
    main()
