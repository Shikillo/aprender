#!/usr/bin/env python3
"""
Prepara la carpeta de la sesión para publicarla con el plugin Digital Garden de Obsidian.

Uso: python3 -I preparar_jardin.py <carpeta_sesión> [--simular]

1. Todas las notas .md de la sesión (salvo carpetas ocultas como .fuentes/ o .latex/) llevan
   `dg-publish: true` en el frontmatter. Si no tienen frontmatter, se les añade. Si una nota
   tiene `dg-publish: false`, se respeta (es una decisión del usuario) y se avisa.
2. `index.md` en la raíz de la sesión es la portada del jardín (`dg-home: true`) y enlaza todas
   las asignaturas: cada carpeta con un `00 <T> - Índice.md`. Las que falten se añaden a la
   sección "## Asignaturas" (se crea si no existe). Nunca se borra nada del index.
   - Si existe `00 Índice general.md` (versiones anteriores) y no hay index.md, se renombra a
     index.md y se actualizan los enlaces que apuntaban a él.
   - Si otra nota ya tiene `dg-home: true`, index.md no se marca como portada y se avisa
     (el plugin solo admite una).
--simular: no escribe nada, solo informa.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import json
import re
import sys
from pathlib import Path

FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?\n)?---[ \t]*(?:\n|\Z)", re.S)
WIKILINK = re.compile(r"\[\[([^\]|#^]+)")


def notas(sesion: Path) -> list[Path]:
    return sorted(p for p in sesion.rglob("*.md")
                  if not any(parte.startswith(".") or parte == "node_modules"
                             for parte in p.relative_to(sesion).parts))


def valor(fm: str, clave: str) -> str | None:
    m = re.search(rf"^{re.escape(clave)}:\s*(.*?)\s*$", fm, re.M)
    return m.group(1).strip("'\"").lower() if m else None


def poner(texto: str, clave: str, val: str = "true") -> str:
    """Añade `clave: val` al frontmatter (creándolo si no hay). No toca una clave que ya exista."""
    m = FRONTMATTER.match(texto)
    if not m:
        return f"---\n{clave}: {val}\n---\n" + texto
    fm = m.group(1) or ""
    if valor(fm, clave) is not None:
        return texto
    return f"---\n{fm}{clave}: {val}\n---\n" + texto[m.end():]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    simular = "--simular" in sys.argv
    sesion = Path(args[0]).expanduser().resolve()
    informe = {"sesion": str(sesion), "publicadas_nuevas": [], "ya_publicadas": 0,
               "no_publicadas_por_decision_del_usuario": [], "index": None,
               "asignaturas_añadidas": [], "avisos": []}

    def escribir(p: Path, texto: str):
        if not simular:
            p.write_text(texto, encoding="utf-8")

    index = sesion / "index.md"
    antiguo = sesion / "00 Índice general.md"
    if antiguo.exists() and not index.exists():
        informe["avisos"].append("«00 Índice general.md» renombrado a «index.md» y enlaces actualizados")
        if not simular:
            antiguo.rename(index)
        for p in notas(sesion):
            if p == antiguo:
                continue
            t = p.read_text(encoding="utf-8")
            nuevo = re.sub(r"\[\[00 Índice general(?=[\]|#])", "[[index", t)
            if nuevo != t:
                escribir(p, nuevo)

    # Portada: solo una nota puede tener dg-home.
    otras_portadas = []
    for p in notas(sesion):
        if p == index:
            continue
        m = FRONTMATTER.match(p.read_text(encoding="utf-8"))
        if m and valor(m.group(1) or "", "dg-home") == "true":
            otras_portadas.append(str(p.relative_to(sesion)))

    # index.md: crear o completar
    temas = sorted((i.parent for i in sesion.glob("*/00 * - Índice.md")), key=lambda d: d.name.lower())
    texto = index.read_text(encoding="utf-8") if index.exists() else f"# {sesion.name}\n"
    informe["index"] = "actualizado" if index.exists() else "creado"
    texto = poner(texto, "dg-publish")
    if otras_portadas:
        informe["avisos"].append("No se marca index.md como portada: ya la es " + ", ".join(otras_portadas))
    else:
        texto = poner(texto, "dg-home")

    enlazados = {e.strip().lower() for e in WIKILINK.findall(texto)}
    faltan = [t for t in temas if f"00 {t.name} - índice".lower() not in enlazados]
    if faltan:
        lineas = [f"- [[00 {t.name} - Índice|{t.name}]]" for t in faltan]
        sec = re.search(r"^##\s+(Asignaturas|Temas)\s*$", texto, re.M | re.I)
        if sec:
            siguiente = re.search(r"^#{1,2}\s", texto[sec.end():], re.M)
            fin = sec.end() + (siguiente.start() if siguiente else len(texto) - sec.end())
            bloque = texto[sec.end():fin].rstrip("\n")
            texto = texto[:sec.end()] + bloque + "\n" + "\n".join(lineas) + "\n\n" + texto[fin:].lstrip("\n")
        else:
            texto = texto.rstrip("\n") + "\n\n## Asignaturas\n\n" + "\n".join(lineas) + "\n"
        informe["asignaturas_añadidas"] = [t.name for t in faltan]
    if not index.exists() or texto != index.read_text(encoding="utf-8"):
        escribir(index, texto)

    # dg-publish en todas las notas
    for p in notas(sesion):
        t = p.read_text(encoding="utf-8")
        m = FRONTMATTER.match(t)
        actual = valor(m.group(1) or "", "dg-publish") if m else None
        rel = str(p.relative_to(sesion))
        if actual == "true":
            informe["ya_publicadas"] += 1
        elif actual is not None:
            informe["no_publicadas_por_decision_del_usuario"].append(rel)
        else:
            escribir(p, poner(t, "dg-publish"))
            informe["publicadas_nuevas"].append(rel)

    # Carpetas con notas pero sin índice de aprender: no se enlazan solas, pero se avisan.
    sin_indice = sorted({p.relative_to(sesion).parts[0] for p in notas(sesion)
                         if len(p.relative_to(sesion).parts) > 1} - {t.name for t in temas})
    if sin_indice:
        informe["avisos"].append("Carpetas con notas pero sin «00 <T> - Índice.md» (no se añaden al index): "
                                 + ", ".join(sin_indice))
    informe["publicadas_nuevas_total"] = len(informe["publicadas_nuevas"])
    if len(informe["publicadas_nuevas"]) > 30:
        informe["publicadas_nuevas"] = informe["publicadas_nuevas"][:30] + ["…"]
    print(json.dumps(informe, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
