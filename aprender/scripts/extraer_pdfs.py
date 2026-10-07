#!/usr/bin/env python3
"""
Extrae el texto de TODAS las páginas de los PDFs de una materia, en tramos para leerlos enteros.

Uso: python3 -I extraer_pdfs.py [carpeta | fichero.pdf] [--listar] [--pdf NOMBRE ...] [--tramo N] [--imagenes]

- carpeta: la de la sesión (por defecto, el directorio actual). Ahí se crea UNA CARPETA POR PDF,
  con el nombre del PDF: /Estudios/pdf/Tema1.pdf -> /Estudios/Tema1/ (campo "salida").
- Origen de los PDFs: si la carpeta tiene subcarpetas llamadas pdf, pdfs, PDF… se usan esas
  (recursivamente); si no, todos los PDFs de la carpeta (salvo carpetas ocultas).
- fichero.pdf: solo ese PDF (puede estar fuera); su carpeta de salida se crea en el directorio actual.
- --listar: no extrae nada; lista los PDFs (nombre, páginas, carpeta de salida, si ya tiene apuntes).
- --pdf NOMBRE: solo esos PDFs (se puede repetir). Vale la ruta relativa, el nombre del fichero
  o un trozo del nombre (sin distinguir mayúsculas ni tildes). Sin --pdf, todos.
- Por cada PDF: <salida>/.fuentes/<pdf>/pNNN-MMM.md (tramos de --tramo páginas, 10 por defecto)
  con cabeceras "## Página N", y <salida>/.fuentes/<pdf>.json con los metadatos. Si el PDF no ha
  cambiado, reutiliza la caché.
- --imagenes: además vuelca imágenes de las páginas con poco texto en <salida>/.fuentes/<pdf>/img/
  (la página entera con pdftoppm si está instalado; si no, las imágenes incrustadas).
  Por defecto NO se vuelcan.
- Imprime un manifiesto JSON con el origen y, por PDF, su carpeta de salida, páginas y tramos.
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
    sys.exit("Falta pypdf: `doas apk add py3-pypdf` (Alpine), `sudo apt install python3-pypdf` "
             "(Debian/Ubuntu) o `python3 -m pip install --user pypdf`.")

POCO_TEXTO = 200  # caracteres por página por debajo de los cuales sospechamos imagen/escaneo
NOMBRE_CARPETA_PDF = re.compile(r"^pdfs?$|^pdf[\s_-]", re.I)


def slug(ruta_relativa: Path) -> str:
    s = str(ruta_relativa.with_suffix(""))
    s = re.sub(r"[\\/]+", " - ", s)
    s = re.sub(r"[^\w\s\-.áéíóúüñÁÉÍÓÚÜÑ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def origenes(carpeta: Path) -> list[Path]:
    subs = [d for d in carpeta.iterdir() if d.is_dir() and NOMBRE_CARPETA_PDF.search(d.name)]
    return sorted(subs) or [carpeta]


def buscar_pdfs(carpeta: Path) -> list[Path]:
    pdfs = set()
    for origen in origenes(carpeta):
        for p in origen.rglob("*"):
            oculta = any(parte.startswith(".") for parte in p.relative_to(carpeta).parts[:-1])
            if p.is_file() and p.suffix.lower() == ".pdf" and not oculta:
                pdfs.add(p)
    return sorted(pdfs, key=lambda p: str(p).lower())


def nombre_valido(texto: str) -> str:
    """Nombre de carpeta/nota válido en Obsidian y en cualquier sistema de ficheros."""
    t = re.sub(r'[:/\\#^\[\]|?*<>"]', " ", texto)
    t = re.sub(r"\s+", " ", t).strip(" .")
    return t or "PDF"


def carpetas_salida(pdfs: list[Path], carpeta: Path) -> dict:
    """Una carpeta por PDF, con su nombre, dentro de la carpeta de la sesión.
    Si dos PDFs se llaman igual (en subcarpetas distintas), se añade la subcarpeta: "Tema1 (b)"."""
    base = {p: nombre_valido(p.stem) for p in pdfs}
    repetidos = {n for n in base.values() if list(base.values()).count(n) > 1}
    return {p: carpeta / (f"{n} ({nombre_valido(p.parent.name)})" if n in repetidos else n)
            for p, n in base.items()}


def ruta_pdf(pdf: Path, carpeta: Path) -> str:
    try:
        return str(pdf.relative_to(carpeta))
    except ValueError:  # PDF de fuera de la carpeta de la sesión
        return str(pdf)


def normalizar(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def elegir(pdfs: list[Path], carpeta: Path, pedidos: list[str]) -> list[Path]:
    elegidos = []
    for pedido in pedidos:
        n = normalizar(pedido.strip())
        n_sin_ext = n[:-4] if n.endswith(".pdf") else n
        candidatos = ([p for p in pdfs if normalizar(ruta_pdf(p, carpeta)) == n]
                      or [p for p in pdfs if normalizar(p.name) == n or normalizar(p.stem) == n_sin_ext]
                      or [p for p in pdfs if n_sin_ext in normalizar(p.stem)])
        if not candidatos:
            disponibles = "\n  ".join(ruta_pdf(p, carpeta) for p in pdfs) or "(ninguno)"
            sys.exit(f"Ningún PDF coincide con «{pedido}». Disponibles:\n  {disponibles}")
        if len(candidatos) > 1:
            varios = "\n  ".join(ruta_pdf(p, carpeta) for p in candidatos)
            sys.exit(f"«{pedido}» coincide con varios PDFs; sé más concreto:\n  {varios}")
        if candidatos[0] not in elegidos:
            elegidos.append(candidatos[0])
    return elegidos


def tiene_apuntes(salida: Path, rel: str) -> bool:
    """¿Hay en su carpeta de salida una nota de fuente (de aprender) para este PDF?"""
    if not salida.is_dir():
        return False
    for nota in salida.rglob("*.md"):
        if ".fuentes" in nota.parts:
            continue
        cabecera = nota.read_text(encoding="utf-8", errors="ignore")[:800]
        m = re.search(r"^pdf:\s*(.+)$", cabecera, re.M)
        if "tipo: fuente" in cabecera and m and m.group(1).strip().strip("'\"") == rel:
            return True
    return False


def listar(pdfs: list[Path], carpeta: Path, salidas: dict) -> None:
    filas = []
    for i, pdf in enumerate(pdfs, start=1):
        rel = ruta_pdf(pdf, carpeta)
        try:
            paginas = len(PdfReader(str(pdf)).pages)
        except Exception as e:
            paginas = f"error: {e}"
        filas.append({"n": i, "pdf": rel, "paginas": paginas, "salida": str(salidas[pdf]),
                      "con_apuntes": tiene_apuntes(salidas[pdf], rel)})
    print(json.dumps({"carpeta": str(carpeta), "origen": [str(o) for o in origenes(carpeta)],
                      "pdfs": filas}, ensure_ascii=False, indent=2))
    if not filas:
        sys.exit(1)


def extraer(pdf: Path, carpeta_tramos: Path, tramo: int) -> dict:
    lector = PdfReader(str(pdf))
    n = len(lector.pages)
    if carpeta_tramos.exists():
        shutil.rmtree(carpeta_tramos)
    carpeta_tramos.mkdir(parents=True)
    pocas, total, tramos = [], 0, []
    for inicio in range(1, n + 1, tramo):
        fin = min(inicio + tramo - 1, n)
        partes = []
        for i in range(inicio, fin + 1):
            try:
                texto = (lector.pages[i - 1].extract_text() or "").strip()
            except Exception as e:  # una página corrupta no debe tumbar todo el PDF
                texto = f"[error extrayendo la página: {e}]"
            total += len(texto)
            if len(texto) < POCO_TEXTO:
                pocas.append(i)
            partes.append(f"## Página {i}\n\n{texto or '[sin texto extraíble]'}\n")
        fichero = carpeta_tramos / f"p{inicio:03d}-{fin:03d}.md"
        fichero.write_text(f"# {pdf.name}, páginas {inicio}-{fin} de {n}\n\n" + "\n".join(partes),
                           encoding="utf-8")
        tramos.append(str(fichero))
    return {"paginas": n, "caracteres": total, "paginas_poco_texto": pocas, "tramos": tramos}


def volcar_imagenes(pdf: Path, paginas: list[int], carpeta: Path) -> list[str]:
    carpeta.mkdir(exist_ok=True)
    hechas = []
    if shutil.which("pdftoppm"):
        for n in paginas:
            base = carpeta / f"p{n:03d}"
            subprocess.run(["pdftoppm", "-png", "-r", "110", "-f", str(n), "-l", str(n), "-singlefile",
                            str(pdf), str(base)], check=False, capture_output=True)
            if base.with_suffix(".png").exists():
                hechas.append(str(base.with_suffix(".png")))
        return hechas
    lector = PdfReader(str(pdf))
    for n in paginas:
        try:
            for j, img in enumerate(lector.pages[n - 1].images, start=1):
                destino = carpeta / f"p{n:03d}-{j}{Path(img.name).suffix or '.png'}"
                destino.write_bytes(img.data)
                hechas.append(str(destino))
        except Exception:
            pass  # imagen en un formato que pypdf no sabe extraer: se queda sin volcar
    return hechas


def main():
    args = sys.argv[1:]
    opciones = {"--tramo": "10"}
    posicionales, pedidos = [], []
    i = 0
    while i < len(args):
        if args[i] == "--pdf" and i + 1 < len(args):
            pedidos.append(args[i + 1])
            i += 2
        elif args[i] in opciones and i + 1 < len(args):
            opciones[args[i]] = args[i + 1]
            i += 2
        elif args[i] in ("-h", "--help"):
            sys.exit(__doc__)
        else:
            if not args[i].startswith("--"):
                posicionales.append(args[i])
            i += 1
    con_imagenes = "--imagenes" in args

    objetivo = Path(posicionales[0] if posicionales else ".").expanduser().resolve()
    if objetivo.is_file() and objetivo.suffix.lower() == ".pdf":
        carpeta = Path.cwd().resolve()
        todos = buscar_pdfs(carpeta)
        if objetivo not in todos:
            todos.append(objetivo)
        pdfs = [objetivo]
    else:
        carpeta = objetivo
        todos = pdfs = buscar_pdfs(carpeta)
        if pedidos:
            pdfs = elegir(pdfs, carpeta, pedidos)
    tramo = max(1, int(opciones["--tramo"]))
    # Los nombres se calculan con TODOS los PDFs, para que no cambien según cuáles se elijan.
    salidas = carpetas_salida(todos, carpeta)
    if "--listar" in args:
        listar(pdfs, carpeta, salidas)
        return

    pdfs_info = []
    for pdf in pdfs:
        rel = ruta_pdf(pdf, carpeta)
        cache = salidas[pdf] / ".fuentes"
        cache.mkdir(parents=True, exist_ok=True)
        base = cache / slug(Path(pdf.name))
        meta = base.parent / f"{base.name}.json"  # no with_suffix: "Tema 1.2" perdería el ".2"
        info = {"pdf": rel, "salida": str(salidas[pdf])}
        try:
            previo = json.loads(meta.read_text()) if meta.exists() else None
            if (previo and meta.stat().st_mtime >= pdf.stat().st_mtime and previo.get("tramo") == tramo
                    and all(Path(t).exists() for t in previo.get("tramos", []))):
                datos, info["cache"] = previo, True
            else:
                datos = extraer(pdf, base, tramo)
                datos.update({"pdf": rel, "tramo": tramo})
                info["cache"] = False
            if con_imagenes and datos["paginas_poco_texto"] and not datos.get("imagenes"):
                datos["imagenes"] = volcar_imagenes(pdf, datos["paginas_poco_texto"], base / "img")
            meta.write_text(json.dumps(datos, ensure_ascii=False))
            info.update(datos)
        except Exception as e:
            info["error"] = str(e)
        pdfs_info.append(info)

    salida = {
        "carpeta": str(carpeta),
        "origen": [str(o) for o in origenes(carpeta)],
        "total_pdfs": len(pdfs_info),
        "total_paginas": sum(p.get("paginas", 0) for p in pdfs_info),
        "total_tramos": sum(len(p.get("tramos", [])) for p in pdfs_info),
        "pdfs": pdfs_info,
    }
    print(json.dumps(salida, ensure_ascii=False, indent=2))
    if not pdfs_info:
        print(f"No hay PDFs en {', '.join(salida['origen'])}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
