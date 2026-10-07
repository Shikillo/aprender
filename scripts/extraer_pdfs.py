#!/usr/bin/env python3
"""
Extrae el texto de todos los PDFs de un directorio (recursivo) a ficheros .md cacheados.

Uso: python3 -I extraer_pdfs.py <directorio_materia> <directorio_cache> [--sin-imagenes]

- Un .md por PDF, con cabeceras "## Página N" para poder citar páginas.
- Si el .md cacheado es más nuevo que el PDF, no lo vuelve a extraer.
- Imprime un manifiesto JSON: páginas, caracteres y páginas con poco texto
  (probablemente escaneadas, diagramas o fórmulas).
- De esas páginas guarda imágenes en <cache>/<pdf>.img/ para poder verlas con la herramienta read:
  la página entera si hay `pdftoppm` (poppler); si no, las imágenes incrustadas en la página.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    sys.exit("Falta pypdf: instálalo con `python3 -m pip install pypdf` "
             "o lee los PDFs directamente con la herramienta Read (parámetro pages).")

POCO_TEXTO = 200  # caracteres por página por debajo de los cuales sospechamos imagen/escaneo


def slug(ruta_relativa: Path) -> str:
    s = str(ruta_relativa.with_suffix(""))
    s = re.sub(r"[\\/]+", " - ", s)
    s = re.sub(r"[^\w\s\-.áéíóúüñÁÉÍÓÚÜÑ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def extraer(pdf: Path, destino: Path) -> dict:
    lector = PdfReader(str(pdf))
    partes, pocas = [], []
    total = 0
    for i, pagina in enumerate(lector.pages, start=1):
        try:
            texto = pagina.extract_text() or ""
        except Exception as e:  # páginas corruptas no deben tumbar todo el PDF
            texto = f"[error extrayendo página: {e}]"
        texto = texto.strip()
        total += len(texto)
        if len(texto) < POCO_TEXTO:
            pocas.append(i)
        partes.append(f"## Página {i}\n\n{texto}\n")
    destino.write_text(f"# {pdf.name}\n\n" + "\n".join(partes), encoding="utf-8")
    return {"paginas": len(lector.pages), "caracteres": total, "paginas_poco_texto": pocas}


def volcar_imagenes(pdf: Path, paginas: list[int], carpeta: Path) -> list[str]:
    carpeta.mkdir(exist_ok=True)
    hechas = []
    if shutil.which("pdftoppm"):
        for n in paginas:
            base = carpeta / f"p{n}"
            subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(n), "-l", str(n), "-singlefile",
                            str(pdf), str(base)], check=False, capture_output=True)
            if base.with_suffix(".png").exists():
                hechas.append(str(base.with_suffix(".png")))
        return hechas
    lector = PdfReader(str(pdf))
    for n in paginas:
        try:
            for j, img in enumerate(lector.pages[n - 1].images, start=1):
                destino = carpeta / f"p{n}-{j}{Path(img.name).suffix or '.png'}"
                destino.write_bytes(img.data)
                hechas.append(str(destino))
        except Exception:
            pass  # imagen en un formato que pypdf no sabe extraer: se queda sin volcar
    return hechas


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    con_imagenes = "--sin-imagenes" not in sys.argv
    raiz = Path(args[0]).expanduser().resolve()
    cache = Path(args[1]).expanduser().resolve()
    cache.mkdir(parents=True, exist_ok=True)

    manifiesto = []
    for pdf in sorted(raiz.rglob("*.pdf"), key=lambda p: str(p).lower()):
        if cache in pdf.parents:
            continue
        rel = pdf.relative_to(raiz)
        destino = cache / f"{slug(rel)}.md"
        info = {"pdf": str(rel), "texto": str(destino)}
        meta = destino.with_suffix(".json")
        try:
            if destino.exists() and meta.exists() and destino.stat().st_mtime >= pdf.stat().st_mtime:
                info.update(json.loads(meta.read_text()))
                info["cache"] = True
            else:
                datos = extraer(pdf, destino)
                if con_imagenes and datos["paginas_poco_texto"]:
                    datos["imagenes"] = volcar_imagenes(pdf, datos["paginas_poco_texto"],
                                                        destino.with_suffix(".img"))
                meta.write_text(json.dumps(datos))
                info.update(datos)
                info["cache"] = False
        except Exception as e:
            info["error"] = str(e)
        manifiesto.append(info)

    print(json.dumps(manifiesto, ensure_ascii=False, indent=2))
    if not manifiesto:
        print(f"No hay PDFs en {raiz}", file=sys.stderr)


if __name__ == "__main__":
    main()
