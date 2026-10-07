---
name: 2latex
description: Convierte los apuntes .md de un tema (las notas Obsidian que genera la skill aprender) en un PDF con una plantilla LaTeX, que puede ser la del usuario o una básica incluida. Ordena las notas según la ruta de estudio y convierte enlaces, callouts, fórmulas, tablas y diagramas. Úsala cuando el usuario quiera pasar sus apuntes o un tema a LaTeX o PDF, imprimirlos, maquetarlos con su plantilla o exportarlos fuera de Obsidian.
compatibility: Pi en Linux (también por SSH) o macOS. Necesita python3, pandoc y un compilador de LaTeX (tectonic, o TeX Live con latexmk). Opcional, mmdc (mermaid-cli) para dibujar los diagramas mermaid.
---

# 2latex

Toma la carpeta de un tema (por ejemplo `/Estudios/Tema1/`), mete sus apuntes en una plantilla LaTeX, compila y deja el PDF en `/Estudios/Tema1/Tema1.pdf`.

Uso: `/skill:2latex [tema] [plantilla <ruta>] [autor "<nombre>"] [titulo "<título>"] [sin contraste] [solo tex]`

El script está en `scripts/`, dentro del directorio de esta skill (Pi te dice dónde está). En los comandos, `<skill>` es esa ruta. `<sesión>` es el directorio donde se ha abierto Pi.

**Pregunta lo mínimo.** Lo único que se pregunta es el tema (paso 0). Todo lo demás se decide con los valores por defecto, y al final explicas lo que has decidido.

## Paso 0: qué tema

1. **Si lo ha indicado** (nombre o trozo del nombre de la carpeta, o "todos"), úsalo sin preguntar.
2. **Si no**, busca los temas, que son las carpetas con índice de `aprender`:
   ```bash
   cd "<sesión>" && find . -mindepth 2 -maxdepth 2 -name "00 * - Índice.md" -not -path "*/.*" | sort
   ```
   - Si solo hay uno, úsalo y di cuál es.
   - Si hay varios, pregunta cuál, con `ask_user_question` si existe o en el chat, mediante una lista numerada con la opción "Todos" (un PDF por tema). Marca los que ya tienen PDF (`<T>/<T>.pdf`).
   - Si no hay ninguno, dilo y sugiere generar los apuntes antes con `/skill:aprender`.

## Paso 1: la plantilla

El script la busca en este orden y usa la primera que encuentre:

1. La que se indique con `--plantilla <ruta>`: un `.tex` o una carpeta con el `.tex` y sus ficheros.
2. **`<sesión>/plantilla/`**: una carpeta con el `.tex` principal (con `\documentclass`; si hay varios, `main.tex` o `plantilla.tex`) y sus `.cls`, `.sty`, logos e imágenes. Es el sitio recomendado para la plantilla del usuario.
3. `<sesión>/plantilla.tex`: un fichero suelto. Solo se copian con él los `.cls`, `.sty`, `.bib` e imágenes que tenga al lado.
4. La plantilla básica de la skill (`assets/plantilla-basica/plantilla.tex`).

**Nunca modifiques la plantilla del usuario.** Todo se genera en `<T>/.latex/`.

Marcadores que entiende la plantilla (todos opcionales):

| Marcador | Se sustituye por | Si no está |
|---|---|---|
| `%%2LATEX-PREAMBULO%%` | `\input{2latex-preambulo}`: paquetes y cajas que necesita el contenido | Se pone antes de `\begin{document}` |
| `%%2LATEX-CONTENIDO%%` | `\input{contenido}`: los apuntes | Se pone antes de `\end{document}` |
| `@@TITULO@@` `@@AUTOR@@` `@@FECHA@@` `@@TEMA@@` | El título (por defecto, el nombre del tema), el autor, la fecha (`\today`) y el nombre del tema | Se quedan los valores de la plantilla |

Si la plantilla es de libro (`book`, `report`, `memoir`, `scrbook`, `scrreprt`), el tema empieza con `\chapter{<título>}` y cada concepto es una `\section`.

**"Donde tiene que estar"**: si la plantilla no tiene marcadores y su estructura pide otro sitio (secciones fijas como "Resumen" o "Desarrollo", un entorno propio, una portada que debe ir antes), lee la plantilla y decide dónde va el contenido. Para eso:
1. Ejecuta con `--solo-tex`.
2. Edita `<T>/.latex/main.tex` y mueve `\input{contenido}` (y `\input{2latex-preambulo}` si hace falta) a su sitio.
3. Compila con el mismo comando que usa el script (paso 3).

Al final, dile al usuario qué marcadores puede añadir a su plantilla para que la próxima vez no haga falta.

## Paso 2: convertir y compilar

```bash
cd "<sesión>" && python3 -I <skill>/scripts/md2latex.py "<T>" [--plantilla RUTA] [--titulo "…"] [--autor "…"] [--fecha "…"] [--sin-contraste] [--solo-tex] [--motor auto|pdflatex|xelatex|lualatex|tectonic]
```

Qué hace el script:
- **Orden**: el índice como "Introducción"; los conceptos en el orden de la **ruta de estudio** del índice (los que no estén en ella van después, por `nivel` y nombre); y `01 <T> - Contraste` al final como "Contraste de fuentes" (`--sin-contraste` lo quita). Incluye los conceptos compartidos que viven en la carpeta de otro tema pero citan `Fuente - <T>`. No incluye la nota de fuente, ni el progreso, ni las sesiones.
- **Obsidian a LaTeX**:
  - el frontmatter se quita;
  - `[[enlaces]]` a conceptos del PDF se convierten en referencias internas con hipervínculo, y el resto en texto normal;
  - los callouts pasan a cajas de color con su título;
  - `![[imagen]]` se convierte en una figura;
  - `## Mis notas` vacío se quita y, con contenido, se queda;
  - fórmulas, tablas y listas pasan tal cual;
  - las letras griegas y símbolos (→ ✓ ≤ …) del texto se convierten a LaTeX, y los emojis se quitan.
- **Mermaid**: con `mmdc` se dibuja como figura. Sin él, se convierte en una lista de relaciones ("A → B").
- **Motor**: el que indique la plantilla (`% !TEX program = xelatex`), xelatex si usa `fontspec`, o pdflatex. Compila con latexmk si existe; si no, con tectonic, y si no, con el motor directamente.
- **Resultado**: `<T>/<T>.pdf`, más un resumen JSON con las notas incluidas, los enlaces sin destino, los diagramas y el motor.

**Con "todos"**: ejecuta el script una vez por tema.

## Paso 3: si falla la compilación

El JSON trae `error` (las líneas del log que importan) y `log` (el log completo, en `<T>/.latex/main.log`). Lee el error y arregla la causa, **sin tocar los apuntes ni la plantilla original del usuario**:

| Error típico | Arreglo |
|---|---|
| `File 'x.sty' not found` | Falta un paquete. Con tectonic se descarga solo (necesita internet); con TeX Live, dile al usuario qué paquete instalar |
| `Undefined control sequence` en la plantilla | Es de la plantilla: díselo al usuario con la línea exacta |
| `Undefined control sequence` en `contenido.tex` | Falta una macro de pandoc: añádela con `\providecommand` en `<T>/.latex/2latex-preambulo.tex` y vuelve a compilar a mano |
| `Option clash for package X` | La plantilla y el preámbulo cargan X con opciones distintas: quita X de `2latex-preambulo.tex` en `.latex/` |
| Carácter Unicode no admitido (pdflatex) | Repite con `--motor xelatex` |
| `Missing $ inserted` / `Extra }` | Una fórmula mal escrita en una nota: localízala en `contenido.md` y díselo al usuario (nota y sección). No la corrijas sin decirlo |

Para volver a compilar a mano, desde `<T>/.latex/`, usa el mismo comando que indica `motor` en el JSON (`tectonic --keep-logs main.tex`, o `latexmk -pdf main.tex`, etc.). Después copia `main.pdf` a `<T>/<T>.pdf`. Si tocas `contenido.md`, vuelve a ejecutar el script entero.

Máximo 3 intentos. Si sigue fallando, explica el error al usuario con la línea y la causa probable.

## Paso 4: comprobar y entregar

- Comprueba que el PDF existe y tiene un número de páginas razonable para la cantidad de notas.
- Si `enlaces_sin_destino` incluye conceptos que **deberían** estar (no fuentes ni notas de otros temas), avísalo: puede faltar una nota en `Conceptos/`.
- Al usuario dale:
  - la ruta del PDF;
  - qué plantilla se ha usado y dónde se ha colocado el contenido (marcador o posición deducida);
  - cuántos conceptos lleva, en qué orden;
  - cómo han quedado los diagramas;
  - si estás por SSH (`$SSH_CONNECTION`), la ruta absoluta del PDF para que se lo traiga con `scp` o `rsync`.
