#!/usr/bin/env python3
"""
Busca un término en Wikipedia (y Wikcionario) para contrastar lo que dicen los apuntes.

Uso: python3 -I contrastar.py "<término o pregunta corta>" [--idiomas es,en] [--n 3] [--completo]

Devuelve JSON con, por idioma, los mejores resultados: título, URL y extracto
(introducción del artículo, o el artículo entero con --completo).
Sin dependencias: solo la biblioteca estándar y la API pública de MediaWiki.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import argparse
import json
import sys
import urllib.parse
import urllib.request
import re

UA = "aprender-skill/1.0 (herramienta personal de estudio; contraste de apuntes)"


def api(host: str, params: dict) -> dict:
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode({**params, "format": "json", "formatversion": 2})
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


# Las fórmulas llegan como MathML aplanado (muchas líneas indentadas) seguido de {\displaystyle ...}:
# nos quedamos solo con el LaTeX.
LLAVES = r"(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*"
FORMULA = re.compile(r"[ \t]*(?:\n[ \t]{2,}[^\n]*|\n[ \t]*(?=\n))*?\n[ \t]*\{\\displaystyle ("
                     + LLAVES + r")\}(?:\n[ \t]*(?=\n))*\n?[ \t]*")


def limpiar(texto: str) -> str:
    texto = FORMULA.sub(lambda m: f" ${m.group(1).strip()}$ ", texto)
    return re.sub(r"[ \t]{2,}", " ", texto).strip()


def buscar(host: str, termino: str, n: int, completo: bool) -> list[dict]:
    params = {
        "action": "query", "generator": "search", "gsrsearch": termino, "gsrlimit": n,
        "prop": "extracts|info", "inprop": "url", "explaintext": 1, "redirects": 1,
    }
    if not completo:
        params["exintro"] = 1
    paginas = api(host, params).get("query", {}).get("pages", [])
    paginas.sort(key=lambda p: p.get("index", 0))
    return [{"titulo": p["title"], "url": p.get("fullurl"), "extracto": limpiar(p.get("extract") or "")}
            for p in paginas]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("termino")
    ap.add_argument("--idiomas", default="es,en")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--completo", action="store_true", help="artículo entero en vez de solo la introducción")
    ap.add_argument("--wikcionario", action="store_true", help="buscar también en Wikcionario (definiciones de términos)")
    a = ap.parse_args()

    salida = {"termino": a.termino, "resultados": {}}
    for idioma in [i.strip() for i in a.idiomas.split(",") if i.strip()]:
        hosts = {f"wikipedia_{idioma}": f"{idioma}.wikipedia.org"}
        if a.wikcionario:
            hosts[f"wikcionario_{idioma}"] = f"{idioma}.wiktionary.org"
        for clave, host in hosts.items():
            try:
                salida["resultados"][clave] = buscar(host, a.termino, a.n, a.completo)
            except Exception as e:
                salida["resultados"][clave] = {"error": str(e)}
    json.dump(salida, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
