#!/usr/bin/env python3
"""
Revisa un vault de apuntes estilo Obsidian: enlaces rotos y notas huérfanas.

Uso: python3 -I revisar_enlaces.py <directorio_apuntes>

- Enlace roto: [[X]] donde no existe ninguna nota llamada X (ni alias X).
- Huérfana: nota a la que no enlaza ninguna otra.
- Sin salida: nota de concepto que no enlaza a ninguna otra.
Sale con código 1 si hay enlaces rotos.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import re
import sys
from pathlib import Path

ENLACE = re.compile(r"(?<!!)\[\[([^\]|#^]+)(?:[#^][^\]|]*)?(?:\|[^\]]*)?\]\]")
ALIASES = re.compile(r"^aliases:\s*\[(.*?)\]\s*$|^aliases:\s*$((?:\n\s*-\s*.+)+)", re.M)


def aliases_de(texto: str) -> list[str]:
    if not texto.startswith("---"):
        return []
    fm = texto.split("---", 2)[1] if texto.count("---") >= 2 else ""
    m = ALIASES.search(fm)
    if not m:
        return []
    bruto = m.group(1) if m.group(1) is not None else m.group(2)
    trozos = re.split(r",|\n\s*-\s*", bruto)
    return [t.strip().strip("'\"") for t in trozos if t.strip().strip("'\"")]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    raiz = Path(sys.argv[1]).expanduser().resolve()
    notas = {p: p.read_text(encoding="utf-8") for p in raiz.rglob("*.md")
             if not any(parte.startswith(".") for parte in p.relative_to(raiz).parts)}

    nombres = {}
    for p, texto in notas.items():
        nombres[p.stem.lower()] = p
        nombres[str(p.relative_to(raiz).with_suffix("")).lower()] = p
        for a in aliases_de(texto):
            nombres[a.lower()] = p

    rotos, entrantes, salientes = [], {p: 0 for p in notas}, {p: 0 for p in notas}
    for p, texto in notas.items():
        for destino in ENLACE.findall(texto):
            d = nombres.get(destino.strip().lower())
            if d is None:
                rotos.append((p.relative_to(raiz), destino))
            elif d != p:
                entrantes[d] += 1
                salientes[p] += 1

    huerfanas = [p.relative_to(raiz) for p, n in entrantes.items()
                 if n == 0 and not p.stem.startswith(("00", "_"))]
    sin_salida = [p.relative_to(raiz) for p, n in salientes.items()
                  if n == 0 and "tipo: concepto" in notas[p]]

    print(f"Notas: {len(notas)}")
    print(f"Enlaces rotos: {len(rotos)}")
    for nota, destino in rotos:
        print(f"  {nota} -> [[{destino}]]")
    print(f"Huérfanas (nadie las enlaza): {len(huerfanas)}")
    for h in huerfanas:
        print(f"  {h}")
    print(f"Conceptos sin enlaces de salida: {len(sin_salida)}")
    for s in sin_salida:
        print(f"  {s}")
    sys.exit(1 if rotos else 0)


if __name__ == "__main__":
    main()
