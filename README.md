# aprender + contrastar + 2latex + jardin

Cuatro skills para estudiar a partir de PDFs. Funcionan en [Pi](https://github.com/earendil-works/pi) y en [Claude Code](https://code.claude.com), con los mismos ficheros:

- **[`aprender`](#aprender)** convierte tus PDFs en **apuntes enlazados al estilo Obsidian**, contrasta los datos y después **te enseña la materia** con sesiones guiadas, preguntas tipo test y repaso espaciado.
- **[`contrastar`](#contrastar)** verifica cualquier material (PDF, notas o texto) **afirmación por afirmación** contra Wikipedia y fuentes primarias.
- **[`2latex`](#2latex)** convierte los apuntes de un tema en un **PDF con tu plantilla LaTeX**.
- **[`jardin`](#publicar-como-jardín-digital)** deja cualquier carpeta de notas **lista para publicar** con el plugin Digital Garden de Obsidian.

```
.
├── aprender/      ← SKILL.md + scripts/
├── contrastar/    ← SKILL.md + scripts/
├── 2latex/        ← SKILL.md + scripts/ + assets/ (plantilla básica)
├── jardin/        ← SKILL.md + scripts/
└── instalar.sh    ← enlaza las skills en Claude Code
```

En Pi se escriben como `/skill:aprender`, y en Claude Code como `/aprender`. En este README se usa la forma de Pi.

Se instalan las cuatro con un solo `git clone` (ver [Instalación](#instalación)).

## aprender

```
/skill:aprender
→ ¿De qué PDF quieres aprender?
    1. Tema1.pdf   (24 págs) ✓ ya tiene apuntes
    2. Tema2.pdf   (31 págs)
    3. Todos
```

### Qué hace

**1. Apuntes**
- Lee **todas las páginas** del PDF, sin saltarse ninguna ni suponer lo que dicen. Lleva un registro de lectura página a página, y un script comprueba que no falta ninguna.
- Crea **una carpeta por PDF** con notas atómicas enlazadas con `[[wikilinks]]`: una nota por concepto, ordenadas de las ideas base a las que dependen de ellas.
- Cada nota explica qué problema resuelve el concepto, qué es, cómo se podría haber descubierto, de qué depende, ejemplos, errores comunes y preguntas de autoevaluación plegables. Las fórmulas van en LaTeX y los mapas en mermaid.
- Antes de escribir nada, **te enseña el árbol de las notas** que va a crear y te pregunta si las genera todas o quieres cambiar algo. Después las **crea todas de una vez**, con un solo comando y sin llenarte el terminal con su contenido.
- Ninguna nota se queda vacía: si alguna está incompleta, no se crea ninguna hasta que estén todas bien.
- Cita la página del PDF de cada dato. Lo que añade la IA y no está en el PDF va marcado como *Ampliación*.

**2. Contraste**
- Comprueba definiciones, fórmulas, cifras, fechas y leyes con Wikipedia (español e inglés), y con fuentes primarias si hay búsqueda web: BOE, normas ISO/UNE/RFC, INE, RAE…
- Marca cada concepto como verificado, matizado, con discrepancia o sin fuente.
- Nunca cambia en silencio lo que dice el PDF: si hay una discrepancia, muestra las dos versiones.
- Usa la skill [`contrastar`](#contrastar), que viene en el mismo repo, para comprobar **todas** las afirmaciones, no una muestra.

**3. Estudio**
- Primero hace preguntas para ver hasta dónde sabes, luego te propone un plan con un mapa y, cuando le das el OK, enseña concepto a concepto, comprobando cada uno con una pregunta.
- Programa los repasos a 1, 3, 7, 14, 30 y 60 días.
- Guarda tu progreso y un registro de cada sesión en la carpeta del tema.

Las imágenes de los PDF **no se procesan por defecto**. Las páginas que son solo imagen se anotan, y puedes pedir que se adapten con `imagenes`.

### Uso

Abre Pi o Claude Code en tu carpeta de estudio, con los PDFs dentro de una subcarpeta `pdf/`:

```
/Estudios/
└── pdf/
    ├── Tema1.pdf
    └── Tema2.pdf
```

| Comando | Qué hace |
|---|---|
| `/skill:aprender` | Te pregunta qué PDF y hace los apuntes o empieza a estudiar, según si ya existen |
| `/skill:aprender tema 2` | Usa ese PDF sin preguntar (vale un trozo del nombre, sin importar tildes ni mayúsculas) |
| `/skill:aprender ~/Descargas/libro.pdf` | Un PDF de cualquier sitio; su carpeta se crea donde está abierto el agente |
| `/skill:aprender todos` | Todos los PDFs, cada uno en su carpeta |
| `/skill:aprender tema 2 estudiar` | Sesión de estudio guiada |
| `/skill:aprender repaso` | Repasa lo que toca hoy |
| `/skill:aprender tema 2 contrastar` | Solo vuelve a verificar los datos |
| `/skill:aprender tema 2 imagenes` | Además adapta las imágenes (diagramas, tablas, fórmulas escaneadas) |

Aparte de elegir el PDF, la generación de apuntes no hace preguntas.

### Resultado

Una carpeta por PDF, con su nombre, dentro de la carpeta donde abriste el agente:

```
/Estudios/                       ← ábrela como vault en Obsidian
├── pdf/
├── index.md                     ← portada del jardín digital: enlaza todas las asignaturas
├── Tema1/
│   ├── 00 Tema1 - Índice.md     ← mapa de conceptos, ideas base y ruta de estudio
│   ├── 01 Tema1 - Contraste.md  ← resultado de la verificación
│   ├── _Tema1 - Progreso.md     ← tu progreso y fechas de repaso
│   ├── Fuente - Tema1.md        ← resumen del PDF y registro de lectura
│   ├── Contraste - Tema1.md     ← informe de la skill contrastar
│   ├── Tema1.pdf                ← generado por la skill 2latex
│   ├── Conceptos/               ← una nota por concepto
│   ├── Sesiones/                ← registro de cada sesión de estudio
│   └── .fuentes/                ← texto extraído (caché, oculto en Obsidian)
└── Tema2/
```

Abre **la carpeta de estudio entera** como vault, no cada tema por separado. Los conceptos compartidos entre temas tienen una sola nota, enlazada desde todos, así que los temas quedan conectados en la vista de grafo. Escribe lo tuyo en la sección `## Mis notas` de cada nota: la skill nunca la toca.

## contrastar

Comprueba si lo que dice un material es cierto y está actualizado, afirmación por afirmación, y deja por escrito el resultado con sus fuentes.

| Comando | Qué contrasta |
|---|---|
| `/skill:contrastar` | Te pregunta qué: un PDF, la carpeta de un tema de `aprender` o unas notas |
| `/skill:contrastar tema 2` | Ese PDF |
| `/skill:contrastar Tema2` | Los apuntes de ese tema generados por `aprender` |
| `/skill:contrastar ~/notas/redes.md` | Cualquier nota `.md` |
| `/skill:contrastar "La ley de Ohm dice…"` | Un texto; responde en el chat |

- **Lee todo**: cada página del PDF, con registro de lectura comprobado por script, o cada nota entera.
- **Comprueba todo lo verificable**, no una muestra: definiciones, fórmulas, unidades, cifras, fechas, nombres, artículos de leyes, clasificaciones y frases con "siempre", "todos" o "ningún".
- **Busca la fuente adecuada** para cada dato: Wikipedia en español e inglés y Wikcionario siempre; y, si hay búsqueda web, la fuente primaria (BOE consolidado, EUR-Lex, ISO/UNE/RFC, INE/Eurostat, RAE…). Comprueba también si el dato sigue **vigente**.
- **Clasifica cada afirmación**: ✅ verificado · ℹ️ matizado · ❌ discrepancia (con qué es correcto, por qué y si hay riesgo de examen) · ❓ sin fuente.
- **Nunca toca el original.** Para un PDF crea `Tema1/Contraste - Tema1.md`. En apuntes de `aprender` rellena la sección `## Contraste` de cada nota y `01 Tema1 - Contraste.md`. Para otras notas escribe un informe aparte.

## 2latex

Mete todos los apuntes de un tema en una plantilla LaTeX y genera el PDF: `/Estudios/Tema1/` da `/Estudios/Tema1/Tema1.pdf`.

| Comando | Qué hace |
|---|---|
| `/skill:2latex` | Te pregunta qué tema y genera su PDF |
| `/skill:2latex Tema1` | Ese tema, sin preguntar |
| `/skill:2latex todos` | Un PDF por tema |
| `/skill:2latex Tema1 autor "Juan"` | Con autor (también `titulo "…"`) |
| `/skill:2latex Tema1 sin contraste` | Sin el capítulo de contraste de fuentes |

**Tu plantilla**: ponla en `plantilla/`, dentro de la carpeta de estudio, con sus `.cls`, `.sty` y logos:

```
/Estudios/
├── plantilla/
│   ├── apuntes.tex     ← con \documentclass
│   ├── miestilo.sty
│   └── logo.png
└── Tema1/
```

También vale un `plantilla.tex` suelto, o indicar otra ruta. Si no hay ninguna, usa la plantilla básica incluida (`2latex/assets/plantilla-basica/plantilla.tex`), que sirve de ejemplo.

En tu plantilla puedes poner estos marcadores, todos opcionales:

```latex
%%2LATEX-PREAMBULO%%   % paquetes que necesita el contenido (si falta: antes de \begin{document})
%%2LATEX-CONTENIDO%%   % los apuntes (si falta: antes de \end{document})
@@TITULO@@  @@AUTOR@@  @@FECHA@@  @@TEMA@@
```

Si tu plantilla no tiene marcadores y el contenido debe ir en otro sitio (una sección fija, un entorno propio), la skill lee la plantilla y lo coloca donde corresponde. Tu plantilla nunca se modifica: todo se genera en `Tema1/.latex/`.

**Qué hace con los apuntes:**
- Los ordena según la ruta de estudio: introducción, conceptos y contraste al final.
- Convierte los `[[enlaces]]` en referencias internas con hipervínculo y los callouts en cajas de colores.
- Conserva fórmulas y tablas.
- Dibuja los diagramas mermaid si tienes `mmdc`; si no, los convierte en una lista de relaciones.
- Elige el motor según la plantilla (pdflatex, o xelatex si usa `fontspec`).
- Si la compilación falla, lee el log y lo arregla, o te dice la línea exacta y la causa.

## Instalación

### 1. Requisitos

- [Pi](https://github.com/earendil-works/pi) (necesita Node.js 22.19 o superior), [Claude Code](https://code.claude.com), o los dos.
- Python 3 con `pypdf`.
- Acceso a internet, para el contraste.
- Opcional: `poppler` (`pdftoppm`), para adaptar imágenes como página completa.
- Para `2latex`: `pandoc` y un compilador de LaTeX. Lo más ligero es **tectonic**, que descarga solo los paquetes que necesita (la primera vez tarda unos minutos). La alternativa es TeX Live con `latexmk`.

**Alpine** (3.21 o superior; `py3-pypdf` está en el repositorio *community*):
```sh
doas apk add bash python3 py3-pypdf poppler-utils ca-certificates nodejs npm git tmux
doas apk add pandoc-cli tectonic          # para 2latex
doas npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

**Debian / Ubuntu:**
```sh
sudo apt install python3 python3-pypdf poppler-utils git tmux
sudo apt install pandoc texlive-latex-extra texlive-xetex latexmk   # para 2latex
# Node.js 22.19+ desde nodesource o nvm, y después:
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

**macOS:**
```sh
brew install python poppler node pandoc tectonic && python3 -m pip install --user pypdf
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

### 2. Las skills

Se clona una sola vez y sirve para los dos agentes:

```sh
git clone https://github.com/Shikillo/aprender.git ~/.agents/skills/estudio
```

- **Pi** busca `SKILL.md` en las subcarpetas de `~/.agents/skills/`, así que ya encuentra `aprender`, `contrastar`, `2latex` y `jardin`. Comprueba que aparecen escribiendo `/skill:` en Pi.
- **Claude Code** solo busca en las subcarpetas directas de `~/.claude/skills/`. Ejecuta el instalador, que crea un enlace por skill:
  ```sh
  ~/.agents/skills/estudio/instalar.sh
  ```
  Abre una sesión nueva de Claude Code y escribe `/` para verlas. `./instalar.sh .claude/skills` las instala solo en un proyecto, y `./instalar.sh --quitar` borra los enlaces.

Para actualizarlas (en los dos agentes a la vez, porque Claude Code usa enlaces al mismo repo):
```sh
git -C ~/.agents/skills/estudio pull
```

Para usarlas solo en un proyecto con Pi, clona el repo en `.pi/skills/estudio/` dentro de ese proyecto.

> **Si vienes de una versión anterior** (con la skill en `~/.agents/skills/aprender/` o `contrastar/` copiada aparte), borra esas carpetas antes de clonar. Si no, Pi tendrá dos skills con el mismo nombre.

### 3. Recomendado en Pi: herramientas de learn

En Claude Code no hace falta: ya trae preguntas con opciones (`AskUserQuestion`), búsqueda web (`WebSearch`, `WebFetch`) y subagentes (`Agent`), y las skills los usan directamente.

En Pi, la skill funciona sin nada más: hace las preguntas en el chat y contrasta con Wikipedia. Pero mejora mucho con las extensiones de [amosblomqvist/learn](https://github.com/amosblomqvist/learn), si están instaladas:

| Herramienta | Qué aporta |
|---|---|
| `quiz` | Preguntas tipo test en una ventana que corrige al instante |
| `ask_user_question` | Preguntas abiertas en una ventana |
| agente `researcher` + `web_search` | Contraste con fuentes primarias, no solo Wikipedia |
| subagentes ([pi-interactive-subagents](https://github.com/amosblomqvist/pi-interactive-subagents), necesita tmux) | Lee PDFs grandes en paralelo |

```sh
cd /Estudios && git clone https://github.com/amosblomqvist/learn .pi
```

## Publicar como jardín digital

La carpeta de estudio está lista para publicarse con el plugin [Digital Garden](https://github.com/oleeskild/obsidian-digital-garden) de Obsidian:

- **Todas las notas** llevan `dg-publish: true`: conceptos, índices, fuentes, contraste, progreso y sesiones. Si quieres que una nota no se publique, ponle `dg-publish: false`; las skills lo respetan.
- **`index.md`** es la portada (`dg-home: true`) y enlaza todas las asignaturas. Cada vez que se genera un tema nuevo, se añade a su sección `## Asignaturas` sin tocar lo que hayas escrito en el index.
- Las carpetas ocultas (`.fuentes/`, `.latex/`) no se publican.

`aprender` y `contrastar` lo hacen solas al terminar. Para cualquier otra carpeta (notas tuyas, una carpeta antigua o después de editar a mano) está la skill **`jardin`**:

| Comando | Qué hace |
|---|---|
| `/skill:jardin` | Revisa todas las notas de la carpeta actual y les añade lo que falte para publicarse |
| `/skill:jardin simular` | Solo te dice qué cambiaría, sin tocar nada |
| `/skill:jardin /otra/carpeta` | Lo mismo en otra carpeta |

Además de marcar las notas, completa `index.md` con las asignaturas nuevas (con una descripción de cada una) y te avisa de lo que pueda salir mal al publicar: dos portadas, carpetas sin índice o enlaces a notas que no se publican.

Sin abrir ningún agente, también puedes ejecutar el script directamente:

```sh
python3 -I ~/.agents/skills/estudio/jardin/scripts/preparar_jardin.py /Estudios --simular   # ver qué cambiaría
python3 -I ~/.agents/skills/estudio/jardin/scripts/preparar_jardin.py /Estudios
```

Si tenías un `00 Índice general.md` de una versión anterior, se renombra a `index.md` y se actualizan los enlaces.

## Usarla en un servidor por SSH

El agente (Pi o Claude Code) y las skills funcionan en el servidor, pero Obsidian está en tu ordenador:

- Las skills crean las notas sin imprimirlas en el terminal: las lees en Obsidian. Pi enseña solo las 10 primeras líneas de cada fichero creado; si ves notas enteras, pulsa **Ctrl+O** para plegar la salida de las herramientas.

- Ejecuta Pi o Claude Code dentro de **tmux**, para que una conexión caída no corte la generación de apuntes.
- Para ver los apuntes en Obsidian, sincroniza la carpeta de estudio:
  - **Syncthing** (`apk add syncthing` / `apt install syncthing`): sincroniza en los dos sentidos. Es lo mejor si escribes en `## Mis notas`.
  - **rsync**, en un solo sentido: `rsync -avz --exclude pdf/ usuario@servidor:/Estudios/ ~/Obsidian/Estudios/`
- Si te da `DNS transient error` en Alpine con Tailscale (MagicDNS), ejecuta `doas tailscale set --accept-dns=false` y pon `nameserver 1.1.1.1` y `nameserver 8.8.8.8` en `/etc/resolv.conf`.

## Scripts incluidos

Los usan las skills; no hace falta ejecutarlos a mano. Todos usan solo la biblioteca estándar, salvo `pypdf`.

| Script | En | Para qué |
|---|---|---|
| `extraer_pdfs.py` | las dos | Encuentra los PDFs, los lista (`--listar`), crea la carpeta de cada uno y extrae el texto en tramos de 10 páginas |
| `contrastar.py` | las dos | Busca un término en Wikipedia (español e inglés) y Wikcionario, con las fórmulas en LaTeX |
| `revisar_lectura.py` | las dos | Comprueba que el registro de lectura cubre todas las páginas. En `aprender` mira la nota `Fuente - <T>`; en `contrastar`, el informe `Contraste - <T>` |
| `revisar_enlaces.py` | aprender | Busca enlaces `[[...]]` rotos y notas huérfanas en el vault |
| `preparar_jardin.py` | aprender, contrastar, jardin | Pone `dg-publish: true` en todas las notas y crea o completa `index.md` (portada, `dg-home`) con todas las asignaturas |
| `crear_notas.py` | aprender | Enseña el árbol de notas planeadas (`--arbol`) y, tras la confirmación, crea todas a la vez desde los borradores, comprobando antes que estén completas |
| `revisar_notas.py` | aprender | Detecta notas de concepto vacías o a medias (sin "En una frase", sin "Qué es" desarrollado, sin páginas, secciones vacías…) |
| `md2latex.py` + `callouts.lua` | 2latex | Junta las notas del tema, las convierte con pandoc, rellena la plantilla y compila |

Cada skill lleva su propia copia de los scripts para poder funcionar sola. Si cambias `extraer_pdfs.py`, `contrastar.py` o `preparar_jardin.py`, copia el cambio a todas las carpetas que lo tengan.

## Créditos

La filosofía de enseñanza (primero las verdades incondicionales, "¿cómo podría haberlo descubierto yo?", sondeo → plan → enseñanza, y cómo construir buenas preguntas tipo test) está adaptada de la skill `teach` de [amosblomqvist/learn](https://github.com/amosblomqvist/learn).
