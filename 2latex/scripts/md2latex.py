#!/usr/bin/env python3
"""
Convierte los apuntes de un tema (formato de la skill aprender) en un PDF con una plantilla LaTeX.

Uso: python3 -I md2latex.py <carpeta_tema> [--plantilla RUTA] [--titulo T] [--autor A] [--fecha F]
                            [--sin-contraste] [--solo-tex] [--motor auto|pdflatex|xelatex|lualatex|tectonic]

Pasos:
 1. Junta las notas del tema en orden: el índice como introducción, los conceptos según la
    "ruta de estudio" del índice (los que falten, por nivel y nombre) y el contraste al final.
    Incluye también los conceptos compartidos que viven en la carpeta de otro tema pero citan
    la fuente de este. No incluye la nota de fuente, ni el progreso, ni las sesiones.
 2. Adapta lo propio de Obsidian: frontmatter fuera, [[enlaces]] a referencias internas del
    PDF, callouts a cajas, ![[imágenes]], mermaid (renderizado con mmdc si existe; si no,
    convertido a lista de relaciones), símbolos y emojis que LaTeX no admite.
 3. pandoc -> LaTeX (con scripts/callouts.lua).
 4. Rellena la plantilla: marcadores %%2LATEX-PREAMBULO%%, %%2LATEX-CONTENIDO%% y @@TITULO@@,
    @@AUTOR@@, @@FECHA@@, @@TEMA@@. Sin marcadores: el preámbulo antes de \\begin{document} y el
    contenido antes de \\end{document}.
 5. Compila (latexmk, tectonic o el motor directamente) y deja el PDF en <carpeta_tema>/<tema>.pdf.

Plantilla, por orden: --plantilla; <sesión>/plantilla/ (carpeta con el .tex y sus ficheros);
<sesión>/plantilla.tex; la plantilla básica de la skill. <sesión> es la carpeta padre del tema.

Todo se genera en <carpeta_tema>/.latex/ (oculta en Obsidian). Imprime un resumen JSON.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PLANTILLA_BASICA = SKILL / "assets" / "plantilla-basica" / "plantilla.tex"
PREAMBULO = SKILL / "assets" / "preambulo.tex"
FILTRO = SKILL / "scripts" / "callouts.lua"

MARCA_PREAMBULO = "%%2LATEX-PREAMBULO%%"
MARCA_CONTENIDO = "%%2LATEX-CONTENIDO%%"

TIPOS_CALLOUT = {
    "note": "note", "abstract": "abstract", "summary": "abstract", "tldr": "abstract",
    "info": "info", "todo": "info", "tip": "tip", "hint": "tip", "important": "tip",
    "success": "success", "check": "success", "done": "success",
    "question": "question", "help": "question", "faq": "question",
    "warning": "warning", "caution": "warning", "attention": "warning",
    "failure": "danger", "fail": "danger", "missing": "danger", "danger": "danger",
    "error": "danger", "bug": "danger", "example": "example", "quote": "quote", "cite": "quote",
}
TITULO_POR_DEFECTO = {
    "note": "Nota", "abstract": "Resumen", "info": "Información", "tip": "Consejo",
    "success": "Verificado", "question": "Pregunta", "warning": "Atención", "danger": "Peligro",
    "example": "Ejemplo", "quote": "Cita",
}
# Símbolos frecuentes en los apuntes que pdflatex no sabe componer.
SIMBOLOS_TEXTO = {
    "✓": r"$\checkmark$", "✔": r"$\checkmark$", "✅": r"$\checkmark$", "✗": r"$\times$",
    "✘": r"$\times$", "❌": r"$\times$", "⚠": "(!)", "→": r"$\rightarrow$", "←": r"$\leftarrow$",
    "↔": r"$\leftrightarrow$", "⇒": r"$\Rightarrow$", "⇔": r"$\Leftrightarrow$", "≤": r"$\leq$",
    "≥": r"$\geq$", "≠": r"$\neq$", "≈": r"$\approx$", "×": r"$\times$", "∞": r"$\infty$",
    "±": r"$\pm$", "√": r"$\surd$", "…": "...",
}
SIMBOLOS_MATES = {
    "→": r"\rightarrow ", "←": r"\leftarrow ", "↔": r"\leftrightarrow ", "⇒": r"\Rightarrow ",
    "⇔": r"\Leftrightarrow ", "≤": r"\leq ", "≥": r"\geq ", "≠": r"\neq ", "≈": r"\approx ",
    "×": r"\times ", "·": r"\cdot ", "∞": r"\infty ", "±": r"\pm ", "√": r"\sqrt ",
}
# Letras griegas sueltas en el texto: a fórmula, que las fuentes de texto por defecto no las tienen.
GRIEGAS = dict(zip("αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ",
    r"\alpha \beta \gamma \delta \varepsilon \zeta \eta \theta \iota \kappa \lambda \mu \nu \xi \pi \rho "
    r"\sigma \tau \upsilon \varphi \chi \psi \omega \Gamma \Delta \Theta \Lambda \Xi \Pi \Sigma \Phi \Psi \Omega".split()))
EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")
WIKILINK = re.compile(r"(!?)\[\[([^\]|#^]+)((?:#|\^)[^\]|]*)?(?:\|([^\]]*))?\]\]")
EXTENSIONES_ACOMPANANTES = {".cls", ".sty", ".bst", ".bib", ".bbx", ".cbx", ".def", ".cfg", ".clo",
                            ".png", ".jpg", ".jpeg", ".eps", ".svg", ".ttf", ".otf"}
CLASES_LIBRO = re.compile(r"\\documentclass(\[[^\]]*\])?\{(book|report|memoir|scrbook|scrreprt)\}")


# ---------- notas ----------

def leer_nota(p: Path) -> tuple[dict, str]:
    texto = p.read_text(encoding="utf-8")
    fm, cuerpo = {}, texto
    if texto.startswith("---"):
        partes = texto.split("---", 2)
        if len(partes) == 3:
            cuerpo = partes[2]
            clave = None
            for linea in partes[1].splitlines():
                m = re.match(r"^([\w-]+):\s*(.*)$", linea)
                if m:
                    clave = m.group(1)
                    fm[clave] = m.group(2).strip()
                elif clave and linea.strip().startswith("-"):  # listas YAML en varias líneas
                    fm[clave] = (fm[clave] + " " + linea.strip()[1:].strip()).strip()
    return fm, cuerpo.strip("\n")


def lista_yaml(valor: str) -> list[str]:
    valor = valor.strip().strip("[]")
    return [v.strip().strip("'\"") for v in re.split(r",(?![^\[]*\]\])", valor) if v.strip().strip("'\"")]


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return "c-" + (re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "nota")


def titulo_de(nombre: str, cuerpo: str) -> tuple[str, str]:
    """Quita el '# Título' inicial de la nota y lo devuelve aparte."""
    m = re.match(r"^\s*#\s+(.+?)\s*\n", cuerpo + "\n")
    if m:
        return m.group(1).strip(), cuerpo[m.end():]
    return nombre, cuerpo


def ruta_de_estudio(cuerpo_indice: str) -> list[str]:
    m = re.search(r"^#{1,6}[^\n]*ruta de estudio[^\n]*\n(.*?)(?=^#{1,6}\s|\Z)", cuerpo_indice, re.I | re.M | re.S)
    if not m:
        return []
    return [w.group(2).strip() for w in WIKILINK.finditer(m.group(1)) if not w.group(1)]


def recoger(tema: Path, sin_contraste: bool) -> dict:
    nombre = tema.name
    sesion = tema.parent
    fuente = f"Fuente - {nombre}"

    indice = next(iter(sorted(tema.glob("00 *Índice*.md"))), None)
    contraste = next(iter(sorted(tema.glob("01 *Contraste*.md"))), None)

    conceptos = {}
    for p in sorted(tema.glob("Conceptos/*.md")):
        conceptos[p.stem] = p
    for p in sorted(sesion.glob("*/Conceptos/*.md")):  # compartidos que viven en otro tema
        if p.parent.parent == tema or p.stem in conceptos:
            continue
        fm, _ = leer_nota(p)
        if fuente.lower() in fm.get("fuentes", "").lower():
            conceptos[p.stem] = p

    datos = {n: leer_nota(p) for n, p in conceptos.items()}
    orden = []
    if indice:
        for n in ruta_de_estudio(leer_nota(indice)[1]):
            real = next((c for c in conceptos if c.lower() == n.lower()), None)
            if real and real not in orden:
                orden.append(real)

    def nivel(n):
        try:
            return int(datos[n][0].get("nivel", "99"))
        except ValueError:
            return 99
    resto = sorted((n for n in conceptos if n not in orden), key=lambda n: (nivel(n), n.lower()))
    return {"indice": indice, "contraste": None if sin_contraste else contraste,
            "conceptos": [(n, conceptos[n], datos[n]) for n in orden + resto],
            "en_ruta": len(orden), "fuera_de_ruta": resto}


# ---------- Obsidian -> markdown de pandoc ----------

def trozos(texto: str):
    """Divide en (tipo, texto): 'codigo', 'mates' o 'texto', para no tocar código ni fórmulas al limpiar."""
    patron = re.compile(r"(```.*?```|`[^`\n]+`|\$\$.*?\$\$|(?<![\\$])\$(?!\s)[^$\n]+?(?<!\s)\$)", re.S)
    pos = 0
    for m in patron.finditer(texto):
        if m.start() > pos:
            yield "texto", texto[pos:m.start()]
        t = m.group(0)
        yield ("codigo" if t.startswith("`") else "mates"), t
        pos = m.end()
    if pos < len(texto):
        yield "texto", texto[pos:]


def limpiar_simbolos(texto: str) -> str:
    salida = []
    for tipo, t in trozos(texto):
        if tipo == "texto":
            for s, r in SIMBOLOS_TEXTO.items():
                t = t.replace(s, r)
            for g, cmd in GRIEGAS.items():
                t = t.replace(g, f"${cmd}$")
            t = EMOJI.sub("", t)
        elif tipo == "mates":
            for s, r in SIMBOLOS_MATES.items():
                t = t.replace(s, r)
            for g, cmd in GRIEGAS.items():
                t = t.replace(g, cmd + " ")
        salida.append(t)
    return "".join(salida)


def mermaid_a_lista(codigo: str) -> str:
    """Respaldo sin mmdc: las flechas del diagrama como lista 'A → B'."""
    etiquetas = {}
    nodo = r"([A-Za-z0-9_]+)\s*(?:\[\[?\(?\"?([^\]\)\}\"]*)\"?\)?\]?\]|\(\(?\"?([^\)\"]*)\"?\)?\)|\{\"?([^\}\"]*)\"?\})?"
    for m in re.finditer(nodo, codigo):
        etiqueta = next((g for g in m.groups()[1:] if g), None)
        if etiqueta:
            etiquetas[m.group(1)] = etiqueta.strip()
    flechas = []
    for linea in codigo.splitlines():
        linea = linea.strip()
        if re.match(r"^(graph|flowchart)\b", linea) or not re.search(r"-{2,}>|={2,}>|-\.->", linea):
            continue
        partes = re.split(r"\s*(?:-{2,}>|={2,}>|-\.->)\s*(?:\|[^|]*\|\s*)?", linea)
        ids = [re.match(r"[A-Za-z0-9_]+", p).group(0) for p in partes if re.match(r"[A-Za-z0-9_]+", p)]
        for a, b in zip(ids, ids[1:]):
            flechas.append(f"- {etiquetas.get(a, a)} $\\rightarrow$ {etiquetas.get(b, b)}")
    if not flechas:
        return "*(Diagrama: ver los apuntes en Obsidian.)*"
    return "**Relaciones del diagrama:**\n\n" + "\n".join(dict.fromkeys(flechas))


def convertir_mermaid(texto: str, build: Path, estado: dict) -> str:
    def sustituir(m):
        codigo = m.group(1)
        estado["mermaid"] += 1
        n = estado["mermaid"]
        if shutil.which("mmdc"):
            img = build / "img"
            img.mkdir(exist_ok=True)
            fuente, destino = img / f"mermaid-{n}.mmd", img / f"mermaid-{n}.pdf"
            fuente.write_text(codigo, encoding="utf-8")
            r = subprocess.run(["mmdc", "-i", str(fuente), "-o", str(destino), "--pdfFit"],
                               capture_output=True, text=True)
            if r.returncode == 0 and destino.exists():
                estado["mermaid_renderizados"] += 1
                return f"\n![](img/mermaid-{n}.pdf)\n"
        estado["mermaid_como_lista"] += 1
        return "\n" + mermaid_a_lista(codigo) + "\n"
    return re.sub(r"^```mermaid\s*\n(.*?)^```\s*$", sustituir, texto, flags=re.M | re.S)


def convertir_callouts(texto: str) -> str:
    lineas, salida, i = texto.split("\n"), [], 0
    cabecera = re.compile(r"^>\s*\[!([\w-]+)\]([+-]?)\s*(.*)$")
    while i < len(lineas):
        m = cabecera.match(lineas[i])
        if not m:
            salida.append(lineas[i])
            i += 1
            continue
        tipo = TIPOS_CALLOUT.get(m.group(1).lower(), "note")
        titulo = m.group(3).strip() or TITULO_POR_DEFECTO[tipo]
        i += 1
        cuerpo = []
        while i < len(lineas) and lineas[i].startswith(">"):
            cuerpo.append(re.sub(r"^>\s?", "", lineas[i]))
            i += 1
        salida += ["", f"::: callout-{tipo}", f"[{titulo}]{{.callout-titulo}}", ""]
        salida += convertir_callouts("\n".join(cuerpo)).split("\n")
        salida += ["", ":::", ""]
    return "\n".join(salida)


def convertir_enlaces(texto: str, destinos: dict, sesion: Path, build: Path, estado: dict) -> str:
    def sustituir(m):
        incrustado, objetivo, _, alias = m.groups()
        objetivo = objetivo.strip()
        if incrustado and Path(objetivo).suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".svg", ".webp"):
            encontrado = next((p for p in sesion.rglob(Path(objetivo).name) if ".latex" not in p.parts), None)
            if encontrado:
                (build / "img").mkdir(exist_ok=True)
                shutil.copy2(encontrado, build / "img" / encontrado.name)
                estado["imagenes"] += 1
                return f"![](img/{encontrado.name})"
            estado["imagenes_no_encontradas"].append(objetivo)
            return f"*[imagen no encontrada: {objetivo}]*"
        texto_enlace = (alias or objetivo).strip()
        ident = destinos.get(objetivo.lower())
        if ident:
            estado["enlaces_internos"] += 1
            return f"[{texto_enlace}](#{ident})"
        estado["enlaces_sin_destino"].add(objetivo)
        return texto_enlace
    return WIKILINK.sub(sustituir, texto)


def preparar_nota(cuerpo: str, destinos: dict, sesion: Path, build: Path, estado: dict) -> str:
    # "## Mis notas" vacío fuera; con contenido, se queda.
    cuerpo = re.sub(r"^##\s+Mis notas[ \t]*(?:\n\s*)?(?=^#{1,2}\s|\Z)", "", cuerpo, flags=re.M)
    cuerpo = re.sub(r"^#\s+", "## ", cuerpo, flags=re.M)  # ningún H1 dentro de una nota
    cuerpo = convertir_mermaid(cuerpo, build, estado)
    cuerpo = convertir_callouts(cuerpo)
    cuerpo = convertir_enlaces(cuerpo, destinos, sesion, build, estado)
    return limpiar_simbolos(cuerpo)


# ---------- plantilla y compilación ----------

def buscar_plantilla(sesion: Path, indicada: str | None) -> tuple[Path, bool]:
    """Devuelve (plantilla .tex, si viene de una carpeta propia cuyos ficheros hay que copiar)."""
    candidatas = []
    if indicada:
        candidatas.append(Path(indicada).expanduser().resolve())
    candidatas += [sesion / "plantilla", sesion / "plantilla.tex", PLANTILLA_BASICA]
    for c in candidatas:
        if c.is_file() and c.suffix == ".tex":
            return c, False
        if c.is_dir():
            tex = [p for p in sorted(c.glob("*.tex")) if "\\documentclass" in p.read_text(encoding="utf-8", errors="ignore")]
            preferida = [p for p in tex if p.stem.lower() in ("main", "plantilla", "template")]
            if preferida or tex:
                return (preferida or tex)[0], True
        if indicada and c == candidatas[0]:
            sys.exit(f"No encuentro una plantilla .tex con \\documentclass en {c}")
    sys.exit("No hay plantilla")


def escapar(texto: str) -> str:
    reemplazos = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
                  "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(reemplazos.get(c, c) for c in texto)


def motor_de(plantilla: str, pedido: str) -> str:
    if pedido != "auto":
        return pedido
    m = re.search(r"%\s*!TEX\s+(?:TS-)?program\s*=\s*(\w+)", plantilla, re.I)
    if m:
        return m.group(1).lower()
    if re.search(r"\\usepackage(\[[^\]]*\])?\{(fontspec|unicode-math|polyglossia)\}", plantilla):
        return "xelatex"
    return "pdflatex"


def compilar(build: Path, motor: str) -> tuple[bool, str, str]:
    def correr(cmd):
        return subprocess.run(cmd, cwd=build, capture_output=True, text=True, errors="replace")
    if motor != "tectonic" and shutil.which("latexmk") and shutil.which(motor):
        bandera = {"pdflatex": "-pdf", "xelatex": "-xelatex", "lualatex": "-lualatex"}.get(motor, "-pdf")
        r = correr(["latexmk", bandera, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"])
        usado = f"latexmk {bandera}"
    elif motor != "tectonic" and shutil.which(motor):
        for _ in range(2):  # dos pasadas para el índice y las referencias
            r = correr([motor, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "main.tex"])
            if r.returncode:
                break
        usado = motor
    elif shutil.which("tectonic"):
        r = correr(["tectonic", "--keep-logs", "main.tex"])
        usado = "tectonic (XeTeX)"
    else:
        return False, "ninguno", ("No hay compilador de LaTeX: instala tectonic (`apk add tectonic`, "
                                  "`brew install tectonic`) o TeX Live (latexmk + pdflatex/xelatex).")
    log = build / "main.log"
    texto_log = log.read_text(errors="replace") if log.exists() else (r.stdout + r.stderr)
    ok = r.returncode == 0 and (build / "main.pdf").exists()
    if ok:
        return True, usado, ""
    lineas = texto_log.splitlines()
    errores = [i for i, l in enumerate(lineas) if l.startswith("!") or re.match(r"^\S+\.tex:\d+:", l) or l.startswith("error:")]
    trozo = []
    for i in errores[:3]:
        trozo += lineas[max(0, i - 2):i + 8] + ["…"]
    return False, usado, "\n".join(trozo or lineas[-40:] or (r.stdout + r.stderr).splitlines()[-40:])


def opcion_resaltado() -> list[str]:
    try:
        v = subprocess.run(["pandoc", "--version"], capture_output=True, text=True).stdout.split()[1]
        mayor, menor = (int(x) for x in v.split(".")[:2])
        return ["--syntax-highlighting=none"] if (mayor, menor) >= (3, 8) else ["--no-highlight"]
    except Exception:
        return ["--no-highlight"]


# ---------- principal ----------

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    opciones = {"--plantilla": None, "--titulo": None, "--autor": "", "--fecha": None, "--motor": "auto"}
    posicionales, i = [], 0
    while i < len(args):
        if args[i] in opciones and i + 1 < len(args):
            opciones[args[i]] = args[i + 1]
            i += 2
        else:
            if not args[i].startswith("--"):
                posicionales.append(args[i])
            i += 1
    if not posicionales:
        sys.exit(__doc__)
    if not shutil.which("pandoc"):
        sys.exit("Falta pandoc: `doas apk add pandoc-cli` (Alpine), `sudo apt install pandoc`, `brew install pandoc`.")

    tema = Path(posicionales[0]).expanduser().resolve()
    if not tema.is_dir():
        sys.exit(f"No existe la carpeta del tema: {tema}")
    sesion = tema.parent
    build = tema / ".latex"
    if build.exists():
        shutil.rmtree(build)
    build.mkdir()

    notas = recoger(tema, "--sin-contraste" in args)
    if not notas["conceptos"] and not notas["indice"]:
        sys.exit(f"No hay apuntes en {tema} (ni índice ni Conceptos/).")

    # Destinos de los enlaces internos: cada concepto (y sus aliases) es una sección del PDF.
    destinos = {}
    for nombre, _, (fm, _) in notas["conceptos"]:
        destinos[nombre.lower()] = slug(nombre)
        for a in lista_yaml(fm.get("aliases", "")):
            destinos.setdefault(a.lower(), slug(nombre))
    if notas["indice"]:
        destinos[notas["indice"].stem.lower()] = "c-introduccion"
    if notas["contraste"]:
        destinos[notas["contraste"].stem.lower()] = "c-contraste"

    estado = {"mermaid": 0, "mermaid_renderizados": 0, "mermaid_como_lista": 0, "imagenes": 0,
              "imagenes_no_encontradas": [], "enlaces_internos": 0, "enlaces_sin_destino": set()}
    partes, incluidas = [], []
    if notas["indice"]:
        _, cuerpo = leer_nota(notas["indice"])
        _, cuerpo = titulo_de("", cuerpo)
        partes.append("# Introducción {#c-introduccion}\n\n" + preparar_nota(cuerpo, destinos, sesion, build, estado))
        incluidas.append(notas["indice"].name)
    for nombre, ruta, (fm, cuerpo) in notas["conceptos"]:
        titulo, cuerpo = titulo_de(nombre, cuerpo)
        partes.append(f"# {limpiar_simbolos(titulo)} {{#{slug(nombre)}}}\n\n" + preparar_nota(cuerpo, destinos, sesion, build, estado))
        incluidas.append(str(ruta.relative_to(sesion)))
    if notas["contraste"]:
        _, cuerpo = leer_nota(notas["contraste"])
        _, cuerpo = titulo_de("", cuerpo)
        partes.append("# Contraste de fuentes {#c-contraste}\n\n" + preparar_nota(cuerpo, destinos, sesion, build, estado))
        incluidas.append(notas["contraste"].name)

    (build / "contenido.md").write_text("\n\n".join(partes) + "\n", encoding="utf-8")
    r = subprocess.run(["pandoc", "contenido.md", "-f",
                        "markdown+tex_math_dollars+raw_tex+fenced_divs+bracketed_spans+pipe_tables"
                        "+lists_without_preceding_blankline",
                        "-t", "latex", "--top-level-division=section", "--lua-filter", str(FILTRO),
                        "--wrap=preserve", "-o", "contenido.tex"] + opcion_resaltado(),
                       cwd=build, capture_output=True, text=True)
    if r.returncode:
        sys.exit("pandoc ha fallado:\n" + r.stderr)

    # Plantilla
    plantilla, en_carpeta = buscar_plantilla(sesion, opciones["--plantilla"])
    if plantilla != PLANTILLA_BASICA:
        # Ficheros que acompañan a la plantilla (.cls, .sty, logos…). Si es una carpeta propia, todo
        # su contenido; si es un .tex suelto, solo los ficheros de LaTeX e imágenes de al lado, porque
        # puede estar en la carpeta de la sesión, junto a los temas y los PDFs.
        for p in plantilla.parent.iterdir():
            if p.name.startswith(".") or p == plantilla or (p.suffix.lower() == ".pdf" and p.stem == plantilla.stem):
                continue
            if en_carpeta and p.is_dir():
                shutil.copytree(p, build / p.name, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".*"))
            elif p.is_file() and (en_carpeta or p.suffix.lower() in EXTENSIONES_ACOMPANANTES):
                shutil.copy2(p, build / p.name)
    shutil.copy2(PREAMBULO, build / "2latex-preambulo.tex")
    tex = plantilla.read_text(encoding="utf-8")
    colocacion = {}
    titulo = opciones["--titulo"] or tema.name
    for marca, valor in {"@@TITULO@@": escapar(titulo), "@@AUTOR@@": escapar(opciones["--autor"]),
                         "@@FECHA@@": escapar(opciones["--fecha"]) if opciones["--fecha"] else r"\today",
                         "@@TEMA@@": escapar(tema.name)}.items():
        tex = tex.replace(marca, valor)
    contenido = r"\input{contenido}"
    if CLASES_LIBRO.search(tex):
        contenido = f"\\chapter{{{escapar(titulo)}}}\n" + contenido
    if MARCA_PREAMBULO in tex:
        tex = tex.replace(MARCA_PREAMBULO, r"\input{2latex-preambulo}")
        colocacion["preambulo"] = "marcador"
    else:
        tex = tex.replace(r"\begin{document}", "\\input{2latex-preambulo}\n\\begin{document}", 1)
        colocacion["preambulo"] = "antes de \\begin{document} (sin marcador)"
    if MARCA_CONTENIDO in tex:
        tex = tex.replace(MARCA_CONTENIDO, contenido)
        colocacion["contenido"] = "marcador"
    else:
        tex = tex.replace(r"\end{document}", contenido + "\n\\end{document}", 1)
        colocacion["contenido"] = "antes de \\end{document} (sin marcador)"
    (build / "main.tex").write_text(tex, encoding="utf-8")

    resumen = {
        "tema": str(tema), "plantilla": str(plantilla), "colocacion": colocacion,
        "notas_incluidas": incluidas, "conceptos_en_ruta_de_estudio": notas["en_ruta"],
        "conceptos_fuera_de_ruta": notas["fuera_de_ruta"],
        "enlaces_internos": estado["enlaces_internos"],
        "enlaces_sin_destino": sorted(estado["enlaces_sin_destino"]),
        "mermaid": {"total": estado["mermaid"], "renderizados": estado["mermaid_renderizados"],
                    "como_lista": estado["mermaid_como_lista"]},
        "imagenes": estado["imagenes"], "imagenes_no_encontradas": estado["imagenes_no_encontradas"],
        "tex": str(build / "main.tex"),
    }
    if "--solo-tex" in args:
        resumen["pdf"] = None
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
        return

    motor = motor_de(tex, opciones["--motor"])
    ok, usado, error = compilar(build, motor)
    resumen.update({"motor": usado, "compilado": ok})
    if ok:
        destino = tema / f"{tema.name}.pdf"
        shutil.copy2(build / "main.pdf", destino)
        resumen["pdf"] = str(destino)
    else:
        resumen["error"] = error
        resumen["log"] = str(build / "main.log")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
