#!/usr/bin/env python3
"""
Comprueba que se han leído y registrado TODAS las páginas de todos los PDFs.

Uso: python3 -I revisar_lectura.py [directorio_apuntes] [--pdf RUTA ...]   (por defecto ./apuntes)

--pdf: comprobar solo esos PDFs (el valor "pdf" del manifiesto). Sin --pdf, todos los extraídos.

Cruza los metadatos de .fuentes/*.json (cuántas páginas tiene cada PDF) con la sección
"## Registro de lectura" de cada nota de fuente (frontmatter `tipo: fuente` y `pdf: <ruta>`).
Cada línea del registro empieza por "- p. N" o "- p. N–M". Sale con código 1 si falta algo.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import json
import re
import sys
from pathlib import Path

LINEA = re.compile(r"^\s*[-*]\s*p(?:ág|ag)?s?\.?\s*(\d+)\s*(?:[–—-]\s*(\d+))?", re.I)


def frontmatter(texto: str) -> dict:
    if not texto.startswith("---"):
        return {}
    partes = texto.split("---", 2)
    if len(partes) < 3:
        return {}
    fm = {}
    for linea in partes[1].splitlines():
        if ":" in linea and not linea.startswith((" ", "-")):
            k, v = linea.split(":", 1)
            fm[k.strip()] = v.strip().strip("'\"")
    return fm


def paginas_registradas(texto: str) -> set[int]:
    m = re.search(r"^## Registro de lectura\s*$(.*?)(?=^## |\Z)", texto, re.M | re.S)
    if not m:
        return set()
    vistas = set()
    for linea in m.group(1).splitlines():
        r = LINEA.match(linea)
        if r:
            a = int(r.group(1))
            b = int(r.group(2) or a)
            vistas.update(range(min(a, b), max(a, b) + 1))
    return vistas


def rangos(nums: list[int]) -> str:
    trozos, inicio = [], None
    for i, n in enumerate(nums):
        if inicio is None:
            inicio = n
        if i + 1 == len(nums) or nums[i + 1] != n + 1:
            trozos.append(f"{inicio}" if inicio == n else f"{inicio}-{n}")
            inicio = None
    return ", ".join(trozos)


def main():
    args, solo = sys.argv[1:], set()
    while "--pdf" in args:
        i = args.index("--pdf")
        solo.add(args[i + 1])
        del args[i:i + 2]
    raiz = Path(args[0] if args else "apuntes").expanduser().resolve()
    metas = {}
    for f in (raiz / ".fuentes").glob("*.json"):
        d = json.loads(f.read_text())
        if "pdf" in d and "paginas" in d and (not solo or d["pdf"] in solo):
            metas[d["pdf"]] = d["paginas"]
    if not metas:
        sys.exit(f"No hay metadatos en {raiz / '.fuentes'}: ejecuta antes extraer_pdfs.py")

    notas = {}
    for p in raiz.rglob("*.md"):
        if ".fuentes" in p.parts:
            continue
        texto = p.read_text(encoding="utf-8")
        fm = frontmatter(texto)
        if fm.get("tipo") == "fuente" and fm.get("pdf"):
            notas[fm["pdf"]] = (p, paginas_registradas(texto))

    incompleto = False
    for pdf, total in sorted(metas.items()):
        if pdf not in notas:
            print(f"✗ {pdf}: no hay nota de fuente con `pdf: {pdf}`")
            incompleto = True
            continue
        nota, vistas = notas[pdf]
        faltan = sorted(set(range(1, total + 1)) - vistas)
        if faltan:
            incompleto = True
            print(f"✗ {pdf}: faltan {len(faltan)} de {total} páginas: {rangos(faltan)}  ({nota.relative_to(raiz)})")
        else:
            print(f"✓ {pdf}: {total}/{total} páginas")
    sys.exit(1 if incompleto else 0)


if __name__ == "__main__":
    main()
