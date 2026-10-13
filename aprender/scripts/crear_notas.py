#!/usr/bin/env python3
"""
Enseña el árbol de notas planeadas y, tras la confirmación del usuario, las crea todas de una vez.

Uso:
  python3 -I crear_notas.py <carpeta_tema> --arbol    # enseña el árbol del plan, no crea nada
  python3 -I crear_notas.py <carpeta_tema>            # comprueba los borradores y crea todas las notas

Ficheros de trabajo, en <carpeta_tema>/.borrador/ (oculta en Obsidian):
- plan.json: {"notas": [{"ruta": "Conceptos/Ley de Ohm.md", "nivel": 2, "paginas": "12-14"},
                        {"ruta": "../Tema2/Conceptos/Carga eléctrica.md", "accion": "ampliar"}, ...]}
  La ruta es relativa a la carpeta del tema. "accion": "crear" (por defecto) o "ampliar" (una nota
  que ya existe y se completará con edit; el script no la toca).
- Borradores: lote-01.md, lote-02.md… con varias notas cada uno, separadas por una línea
      <!-- NOTA: Conceptos/Ley de Ohm.md -->
  También vale un fichero suelto con la misma ruta (p. ej. .borrador/Fuente - Tema1.md).

Al crear, comprueba antes de escribir nada:
- que cada nota "crear" del plan tiene borrador, y que no hay borradores fuera del plan;
- que ninguna nota "crear" existe ya (nunca sobrescribe; esas van como "ampliar");
- que los nombres son válidos en Obsidian;
- que las notas de concepto están completas (las mismas reglas que revisar_notas.py).
Si algo falla, no crea nada y dice qué arreglar. Si todo va bien, crea las notas (con
dg-publish: true), borra .borrador/ e imprime el árbol de lo creado.
"""
from __future__ import annotations  # anotaciones list[...] también en Python 3.7/3.8
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

MARCA = re.compile(r"^<!--\s*NOTA:\s*(.+?)\s*-->\s*$", re.M)
PROHIBIDOS = re.compile(r'[:\\#^\[\]|?*<>"]')
FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?\n)?---[ \t]*(?:\n|\Z)", re.S)


def cargar_revisar_notas():
    ruta = Path(__file__).resolve().parent / "revisar_notas.py"
    spec = importlib.util.spec_from_file_location("revisar_notas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def leer_plan(borrador: Path) -> list[dict]:
    plan = borrador / "plan.json"
    if not plan.exists():
        sys.exit(f"No hay plan: escribe primero {plan}")
    try:
        datos = json.loads(plan.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"plan.json no es JSON válido: {e}")
    notas = datos["notas"] if isinstance(datos, dict) else datos
    for n in notas:
        n.setdefault("accion", "crear")
        n["ruta"] = n["ruta"].replace("\\", "/").lstrip("/")
    return notas


def leer_borradores(borrador: Path) -> dict[str, str]:
    textos = {}
    for lote in sorted(borrador.glob("lote-*.md")):
        contenido = lote.read_text(encoding="utf-8")
        trozos = MARCA.split(contenido)
        # trozos = [antes, ruta1, texto1, ruta2, texto2, ...]
        for i in range(1, len(trozos), 2):
            textos[trozos[i].strip()] = trozos[i + 1].strip("\n") + "\n"
    for p in sorted(borrador.rglob("*.md")):
        rel = p.relative_to(borrador).as_posix()
        if p.name.startswith("lote-") or rel.startswith("."):
            continue
        textos[rel] = p.read_text(encoding="utf-8")
    return textos


def con_dg_publish(texto: str) -> str:
    m = FRONTMATTER.match(texto)
    if not m:
        return "---\ndg-publish: true\n---\n" + texto
    fm = m.group(1) or ""
    if re.search(r"^dg-publish:", fm, re.M):
        return texto
    return f"---\n{fm}dg-publish: true\n---\n" + texto[m.end():]


def arbol(rutas: list[str], etiquetas: dict[str, str], raiz: str) -> str:
    """Dibuja un árbol tipo `tree` con las rutas (relativas a la carpeta del tema)."""
    nodos: dict = {}
    for r in rutas:
        actual = nodos
        partes = r.split("/")
        for parte in partes[:-1]:
            actual = actual.setdefault(parte + "/", {})
        actual[partes[-1]] = None
    lineas = [raiz]

    def pintar(rama: dict, prefijo: str, camino: str):
        claves = sorted(rama, key=lambda k: (not k.endswith("/"), k.lower()))
        for i, k in enumerate(claves):
            ultimo = i == len(claves) - 1
            ruta = camino + k
            extra = f"   ({etiquetas[ruta]})" if ruta in etiquetas else ""
            lineas.append(f"{prefijo}{'└── ' if ultimo else '├── '}{k}{extra}")
            if rama[k] is not None:
                pintar(rama[k], prefijo + ("    " if ultimo else "│   "), ruta)
    pintar(nodos, "", "")
    return "\n".join(lineas)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    tema = Path(args[0]).expanduser().resolve()
    borrador = tema / ".borrador"
    plan = leer_plan(borrador)
    crear = [n for n in plan if n["accion"] == "crear"]
    ampliar = [n for n in plan if n["accion"] == "ampliar"]

    if "--arbol" in sys.argv:
        etiquetas = {}
        for n in crear:
            trozos = []
            if "nivel" in n:
                trozos.append(f"nivel {n['nivel']}")
            if n.get("paginas"):
                trozos.append(f"p. {n['paginas']}")
            if (tema / n["ruta"]).exists():
                trozos.append("¡YA EXISTE!")
            if trozos:
                etiquetas[n["ruta"]] = " · ".join(trozos)
        print(arbol([n["ruta"] for n in crear], etiquetas, f"{tema.name}/"))
        conceptos = sum(1 for n in crear if n["ruta"].startswith("Conceptos/"))
        print(f"\n{len(crear)} notas nuevas ({conceptos} conceptos)", end="")
        if ampliar:
            print(f" y {len(ampliar)} que ya " + ("existe y se ampliará:" if len(ampliar) == 1 else "existen y se ampliarán:"))
            for n in ampliar:
                print(f"  ~ {(tema / n['ruta']).resolve().relative_to(tema.parent)}")
        else:
            print()
        return

    textos = leer_borradores(borrador)
    errores = []
    planeadas = {n["ruta"] for n in crear}
    for r in sorted(planeadas - set(textos)):
        errores.append(f"falta el borrador de {r}")
    for r in sorted(set(textos) - planeadas):
        errores.append(f"borrador fuera del plan: {r} (añádelo al plan y díselo al usuario, o bórralo)")
    for r in sorted(planeadas):
        if (tema / r).exists():
            errores.append(f"ya existe {r}: no se sobrescribe; ponla como \"ampliar\" y complétala con edit")
        if PROHIBIDOS.search(Path(r).name):
            errores.append(f"nombre no válido en Obsidian: {r}")

    revisar = cargar_revisar_notas()
    prueba = borrador / ".comprobar.md"
    for r in sorted(planeadas & set(textos)):
        prueba.write_text(textos[r], encoding="utf-8")
        for problema in revisar.revisar(prueba, 80) or []:
            errores.append(f"{r}: {problema}")
    prueba.unlink(missing_ok=True)

    if errores:
        print("No se ha creado ninguna nota. Arregla los borradores y vuelve a ejecutar:")
        for e in errores:
            print(f"  ✗ {e}")
        sys.exit(1)

    for r in sorted(planeadas):
        destino = tema / r
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(con_dg_publish(textos[r]), encoding="utf-8")
    shutil.rmtree(borrador)

    palabras = {r: "%d palabras" % len(re.findall(r"\w+", textos[r])) for r in planeadas}
    print(arbol(sorted(planeadas), palabras, f"{tema.name}/"))
    print(f"\n✓ {len(planeadas)} notas creadas.", end="")
    if ampliar:
        print(f" Queda{'' if len(ampliar) == 1 else 'n'} {len(ampliar)} por ampliar con edit:")
        for n in ampliar:
            print(f"  ~ {(tema / n['ruta']).resolve().relative_to(tema.parent)}")
    else:
        print()


if __name__ == "__main__":
    main()
