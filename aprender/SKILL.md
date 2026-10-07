---
name: aprender
description: Convierte una carpeta de PDFs (temarios, apuntes, libros, diapositivas) en un vault de apuntes .md enlazados al estilo Obsidian ([[wikilinks]], mapa de dependencias, preguntas de autoevaluación), contrasta los datos con Wikipedia y otras fuentes externas, y después enseña la materia con sesiones guiadas (sondeo, plan, enseñanza nodo a nodo, quiz y repaso espaciado). Úsala cuando el usuario quiera estudiar o aprender una materia a partir de PDFs, hacer apuntes o resúmenes enlazados, verificar unos apuntes, preparar un examen o repasar apuntes generados antes.
compatibility: Pi en Linux (también por SSH) o macOS. Necesita python3 con pypdf y acceso a internet para el contraste. Opcional pero recomendado, las extensiones quiz y ask_user_question y el agente researcher de github.com/amosblomqvist/learn. Opcional, pdftoppm (poppler) para adaptar imágenes.
---

# Aprender una materia a partir de PDFs

Dos fases, que pueden hacerse por separado:

1. **Apuntes**: leer los PDFs, construir un vault de notas atómicas enlazadas y **contrastar** los datos con fuentes externas.
2. **Estudiar**: enseñar la materia usando esos apuntes como mapa, y registrar el progreso.

Uso: `/skill:aprender [PDF o carpeta] [apuntes | contrastar | estudiar | repaso] [imagenes]`
- **Carpeta de la sesión** (`<sesión>`): el directorio donde se ha abierto Pi. No preguntes cuál.
- **Dónde van los apuntes**: **una carpeta por PDF**, con el nombre del PDF, dentro de la carpeta de la sesión. Si abres Pi en `/Estudios` y eliges `/Estudios/pdf/Tema1.pdf`, las notas van a `/Estudios/Tema1/`. El extractor da esa ruta en el campo `salida`; úsala siempre, sin inventar otra. En adelante, `<T>` es el nombre de esa carpeta.
- **PDF**: es el dato de entrada de la skill; ver "Paso 0: pedir el PDF".
- **Qué hacer**: `apuntes`, o el PDF elegido aún no tiene apuntes (`con_apuntes: false`) → fase 1. Al terminar, ofrece la fase 2.
- `contrastar` → solo el paso 5, sobre unos apuntes que ya existen.
- `estudiar` / `repaso`, o el PDF elegido ya tiene apuntes → fase 2. Si el extractor detecta PDFs nuevos o modificados (`"cache": false`), actualiza primero los apuntes de esos PDFs sin preguntar.
- `imagenes` (o si el usuario pide adaptar o describir las imágenes) → además de leer todo el texto, se adaptan las imágenes (ver paso 1).

## Paso 0: pedir el PDF (siempre lo primero)

La skill trabaja sobre el PDF, o los PDFs, que elija el usuario.

1. **Si ya lo ha indicado** al invocarla (una ruta a un `.pdf`, un nombre o un trozo del nombre, por ejemplo `/skill:aprender tema 3` o `/skill:aprender ~/Descargas/libro.pdf`, o "todos"), úsalo directamente, sin volver a preguntar.
2. **Si no**, lista los PDFs disponibles:
   ```bash
   cd "<sesión>" && python3 -I <skill>/scripts/extraer_pdfs.py --listar
   ```
   Si la carpeta tiene una subcarpeta `pdf`, `pdfs`, `PDF`… los busca ahí (también en sus subcarpetas); si no, en toda la carpeta. Devuelve cada PDF con su número, sus páginas, su carpeta de `salida` y `con_apuntes` (si ya tiene apuntes en esa carpeta).
3. **Pregunta de cuál quiere aprender**, con `ask_user_question` si existe o en el chat. Muestra una lista numerada con el nombre, las páginas, la carpeta donde irán los apuntes y una marca ✓ en los que ya los tienen, y añade la opción "Todos" (una carpeta para cada uno). Puede responder con el número, el nombre o varios ("1 y 3").
   - Si solo hay un PDF, no preguntes: úsalo y di cuál es.
   - Si no hay ninguno, dilo y explica dónde ponerlos (una subcarpeta `PDF/` en la carpeta actual).
4. Lo elegido se pasa al resto de comandos con `--pdf "<nombre>"` (se puede repetir). Con "Todos", sin `--pdf`.

En la fase 2 se pregunta lo mismo: el PDF del que quiere estudiar. Así, el sondeo, el plan y los repasos se limitan a los conceptos de esa fuente (los que tienen esa nota en `fuentes:`).

**Pregunta lo mínimo.** Aparte del paso 0, la fase 1 se hace entera sin preguntar nada: decide con los valores por defecto y explica al final lo que has decidido. Solo para si no hay ningún PDF o si un paso falla y no tiene arreglo. En la fase 2, las únicas preguntas son las del método (el quiz de sondeo y de comprobación, y el visto bueno al plan).

Los scripts están en `scripts/`, dentro del directorio de esta skill (Pi te dice dónde está). En los comandos de abajo, `<skill>` es esa ruta. Ejecútalos siempre con `python3 -I`.

Escribe los apuntes **en el idioma del material** (normalmente español) y habla con el usuario en su idioma.

## Herramientas según lo que haya instalado

Comprueba qué herramientas tienes y usa la mejor disponible:

| Para | Si existe | Si no |
|---|---|---|
| Preguntas con respuesta correcta | `quiz` (de amosblomqvist/learn) | Pregunta en el chat con opciones A/B/C/D y corrige tú después |
| Preguntas abiertas (objetivo, preferencias) | `ask_user_question` | Pregunta en el chat |
| Investigar o contrastar en la web | subagente `researcher`, o `web_search` / `web_fetch` | `scripts/contrastar.py` (Wikipedia) y `curl` |
| Leer en paralelo mucho material | herramienta de subagentes | Hazlo tú, PDF a PDF |
| Adaptar imágenes (solo si se pide) | `read` sobre las imágenes que genera el extractor con `--imagenes` | Sin `pdftoppm` solo salen las imágenes incrustadas; para la página entera, poppler (`doas apk add poppler-utils` en Alpine; `sudo apt install poppler-utils` en Debian/Ubuntu; `brew install poppler` en macOS) |

Si está instalada la skill `teach` de amosblomqvist/learn, la fase 2 sigue sus reglas. Lo que pone aquí es un resumen compatible con ella.

## Filosofía: comprender, no memorizar

Esta es la base de las dos fases (adaptada de `teach`, amosblomqvist/learn).

Un hecho suelto se olvida. Un hecho que se *deduce* de unas pocas verdades básicas que ya aceptas se queda, porque está sujeto por sus conexiones. Comprender es tener ese **grafo de dependencias** en la cabeza: **nodos** (conceptos) y **aristas** (por qué uno se sigue del otro). Los apuntes son ese grafo hecho fichero; las notas de Obsidian son los nodos y los `[[enlaces]]` las aristas.

- **Principio 1: primero las verdades incondicionales.** Empieza por lo que se puede aceptar tal cual, sin matices: definiciones de verdad (no una lista de propiedades que suelen cumplirse), enunciados universales ("todo X es Y", "ningún X es Y"), unidades atómicas ("TODA comunicación entre ordenadores se hace mediante {paquetes}"). Si algo necesita "normalmente…", aún no es una verdad base: baja un nivel.
- **Principio 2: "¿cómo podría haberlo descubierto yo?"** Lo que parece arbitrario no se fija. Cada paso tiene que estar motivado: qué problema nos obliga a ir por aquí, por qué *esta* fórmula, qué llevaría a alguien a este enfoque. El estilo de referencia es 3Blue1Brown.
- **El "clic"** es el objetivo: muchos hechos sueltos que se reducen a unas pocas ideas que los generan.
- **La exactitud no se negocia.** Una raíz falsa contamina todo lo que cuelga de ella. Por eso los apuntes se contrastan (paso 5) y durante la enseñanza se verifica lo dudoso antes de decirlo.

## Fase 1: generar los apuntes

### 1. Localizar y extraer

```bash
cd "<sesión>" && python3 -I <skill>/scripts/extraer_pdfs.py --pdf "<elegido>"
```

En lugar de `--pdf`, también vale pasar la ruta del fichero directamente: `extraer_pdfs.py "<ruta>/libro.pdf"`. Aunque el PDF esté fuera, su carpeta se crea en la de la sesión. Otras opciones: `--imagenes` (solo si se ha pedido adaptar imágenes) y `--tramo N` (páginas por tramo, 10 por defecto).

Crea la carpeta `<T>/` de cada PDF elegido y parte el PDF en **tramos** de 10 páginas: `<T>/.fuentes/<pdf>/p001-010.md`, `p011-020.md`… con cabeceras `## Página N`. El manifiesto JSON dice de dónde ha sacado los PDFs (`origen`) y, para cada uno, su `salida`, sus `paginas` y la lista de `tramos`. Si un PDF no ha cambiado, reutiliza la caché.

- **Imágenes: por defecto no se adaptan.** Las páginas de `paginas_poco_texto` (escaneadas, solo imagen o casi sin texto) se registran igualmente (paso 2), anotando "poco texto: posible imagen". Al final dile al usuario cuáles son, en una línea, y que puede pedir `imagenes` para adaptarlas. No lo preguntes durante el proceso.
- **Si se piden imágenes**: ejecuta con `--imagenes`. Las imágenes van a `<T>/.fuentes/<pdf>/img/` (lista `imagenes`). Ábrelas con `read` y adapta su contenido (diagramas descritos o rehechos en mermaid, tablas en markdown, fórmulas en LaTeX), citando la página. No inventes lo que no se ve.
- Si falta `pypdf`, pide al usuario que lo instale con el gestor del sistema: `doas apk add py3-pypdf` en Alpine o `sudo apt install python3-pypdf` en Debian/Ubuntu. Usa `python3 -m pip install --user pypdf` solo si no hay paquete, porque pip suele dar el error `externally-managed-environment`.
- La carpeta `.fuentes/` empieza por punto, así que Obsidian no la muestra.

### 2. Leer todo, página a página, e inventariar

**Regla absoluta: se lee cada página de cada PDF.** Nada de leer el índice o el principio y suponer de qué tratará el resto. Nada de saltarse páginas que "parecen" repetidas, de relleno o poco importantes. Lo que hay en una página solo se sabe leyéndola.

- Lee los tramos **uno a uno, en orden y enteros** (con `read`; si un tramo sale truncado, sigue con `offset` hasta el final).
- Después de cada tramo, añade sus páginas al **registro de lectura** de la nota de fuente (ver paso 4): qué hay en cada página o grupo de páginas y qué conceptos aparecen. Si una página no aporta nada nuevo (portada, índice, página en blanco, repetición), regístrala igual, diciendo qué es. Solo puedes saber eso si la has leído.
- No pases a escribir las notas de concepto hasta haber leído todos los tramos de todos los PDFs, porque un concepto puede completarse o matizarse más adelante.

Para cada fuente, saca un inventario:
- conceptos, con su definición literal y las páginas donde aparecen;
- de qué otros conceptos depende cada uno;
- ejemplos, fórmulas, procedimientos, fechas, cifras y errores típicos que señale el material;
- la estructura del documento (temas y capítulos).

**Mucho material** (más de unos 150 páginas, o muchos PDFs) y hay subagentes: lanza uno por PDF o bloque de tramos, en paralelo. Cada uno tiene que leer **todos** sus tramos enteros y devolver dos cosas:
1. el registro de lectura de **cada página** de su parte (`- p. N: …`), sin huecos;
2. el inventario: `concepto | aliases | definición (cita) | páginas | depende de | datos verificables | ejemplos | errores típicos`.

Los subagentes no ven esta conversación: dales las rutas de los tramos, esta regla de leerlo todo y el formato exacto. Si un registro devuelto tiene huecos, vuelve a lanzar esas páginas.

### 3. Unificar y construir el grafo

- **Quita duplicados**: el mismo concepto con nombres distintos es **una sola nota**; los otros nombres van a `aliases`. Si dos PDFs se contradicen, apúntalo para el paso 5.
- **Granularidad**: una nota por concepto que merezca explicarse por sí solo. Ni una por cada término menor, ni un tema entero en una nota.
- **Ordena por dependencias**: las raíces son verdades incondicionales y definiciones. Pon a prueba cada raíz: ¿se acepta tal cual, o se deduce de algo más simple? Si se deduce, bájala y añade el nodo de debajo. El orden topológico es la **ruta de estudio**.
- `nivel`: 0 para las raíces; para el resto, 1 más que el mayor nivel de sus dependencias.

### 4. Escribir el vault

Cada PDF tiene su carpeta `<T>/` dentro de la carpeta de la sesión. Por ejemplo, con Pi abierto en `/Estudios`:

```
/Estudios/                       ← carpeta de la sesión = vault de Obsidian
├── pdf/
│   ├── Tema1.pdf
│   └── Tema2.pdf
├── 00 Índice general.md         ← enlaza los índices de todos los temas
├── Tema1/
│   ├── 00 Tema1 - Índice.md     ← mapa, ruta de estudio, verdades base
│   ├── 01 Tema1 - Contraste.md  ← informe de verificación (paso 5)
│   ├── _Tema1 - Progreso.md     ← lo rellena la fase 2
│   ├── Fuente - Tema1.md        ← resumen del PDF, estructura y registro de lectura
│   ├── Conceptos/
│   │   └── <Concepto>.md
│   ├── Sesiones/
│   │   └── Tema1 AAAA-MM-DD.md  ← registro de cada sesión de estudio
│   └── .fuentes/                ← texto extraído e imágenes (caché, oculto en Obsidian)
└── Tema2/
    └── …
```

**Los nombres de nota no se repiten en toda la carpeta de la sesión**, porque Obsidian enlaza por nombre y dos notas con el mismo nombre rompen los enlaces. Por eso los índices, el contraste, el progreso y las sesiones llevan `<T>` en el nombre. Y, sobre todo:

- **Conceptos compartidos entre temas**: antes de crear `<T>/Conceptos/X.md`, busca si ya existe una nota X (o una con X en sus `aliases`) en la carpeta de otro tema (`find "<sesión>" -path "*/Conceptos/*.md" -not -path "*/.*"`). Si existe, **no la dupliques**: amplía esa nota (añade esta fuente a `fuentes:` y sus páginas a `## Fuentes`, y lo nuevo que aporte este PDF, según las reglas del paso 6) y enlázala desde este tema con `[[X]]`. Así los temas quedan enlazados entre sí.
- **`00 Índice general.md`** en la carpeta de la sesión: una línea por tema con `[[00 <T> - Índice]]` y de qué trata. Créalo o actualízalo cada vez que se añade un tema.

**Reglas de Obsidian:**
- El nombre del fichero es el título, en lenguaje natural ("Ley de Ohm.md"). Prohibido en nombres: `: / \ # ^ [ ] | ? * < > "`.
- Enlaces: `[[Ley de Ohm]]`, `[[Ley de Ohm|la ley]]` o `[[Ley de Ohm#Ejemplo]]`. No hace falta poner la carpeta.
- **Enlaza en línea dentro del texto** la primera vez que se menciona otro concepto, no solo en las listas del final.
- Las matemáticas en LaTeX: `$V = IR$` en línea y `$$ … $$` en bloque. Nunca escribas `V = I*R` como texto plano.
- Los diagramas en bloques ` ```mermaid `.
- Callouts: `> [!abstract]`, `> [!example]`, `> [!warning]`, `> [!info]`, `> [!success]`, `> [!danger]`, y `> [!question]-` (plegado, con la respuesta oculta).
- Etiquetas: `materia/<asignatura>`, `tema/<tema>`.

**Plantilla de nota de concepto** (las secciones que no aporten nada se quitan):

```markdown
---
tipo: concepto
aliases: [Otro nombre]
tags: [materia/<asignatura>, tema/<tema>]
nivel: 1
fuentes: ["[[Fuente - <T>]]"]
contraste: pendiente
estado: nuevo
---
# <Concepto>

> [!abstract] En una frase
> <la idea esencial, que se pueda aceptar tal cual>

## ¿Qué problema resuelve?
<la motivación (principio 2)>

## Qué es
<definición precisa y explicación, con [[enlaces]] en línea>

## Cómo podrías haberlo descubierto
<el camino motivado desde [[sus dependencias]] hasta aquí>

## Depende de
- [[A]]: <qué aporta A para entender esto>

## Permite entender
- [[C]]: <por qué C se apoya en esto>

## Ejemplo
> [!example]
> <ejemplo concreto, idealmente el del material, con su página>

## Errores comunes
> [!warning]
> <confusiones típicas y con qué concepto se confunde>

## Autoevaluación
> [!question]- <pregunta que obligue a razonar, no a recitar>
> <respuesta, con su porqué>

## Contraste
<lo rellena el paso 5>

## Fuentes
- [[Fuente - <T>]], p. 12–14

## Mis notas
```

**`00 <T> - Índice.md`**: de qué va el PDF y su idea central; las **verdades base** (nivel 0) con su frase; el **mapa de dependencias** en mermaid (`graph TD`, raíces arriba; si hay más de unos 25 nodos, un mapa por tema y otro global de temas); la **ruta de estudio** numerada en orden topológico; un índice por tema; y enlaces a `[[Fuente - <T>]]`, a `[[01 <T> - Contraste]]` y a los conceptos de otros temas que use.

**Nota de fuente** (`<T>/Fuente - <T>.md`):

```markdown
---
tipo: fuente
pdf: <el valor "pdf" del manifiesto, tal cual, p. ej. PDFs/tema1/Redes.pdf>
paginas: 48
---
# Fuente - <T>

<resumen de 5 a 10 líneas>

## Estructura
- Capítulo 1, p. 3–12: [[Concepto A]], [[Concepto B]]

## Registro de lectura
- p. 1: portada
- p. 2: índice
- p. 3–4: definición de [[Concepto A]] y ejemplo
- p. 5: [[Concepto B]]; tabla de valores típicos
- p. 17: poco texto, posible imagen (diagrama sin adaptar)
```

El **registro de lectura** cubre todas las páginas, de la 1 a la última. Cada línea empieza por `- p. N` o `- p. N–M`. Es la prueba de que se ha leído todo, y `revisar_lectura.py` lo comprueba.

**Fidelidad**: lo que pongas en "Qué es", "Ejemplo" y "Fuentes" tiene que salir de los PDFs, citando la página. Lo que añadas tú (una intuición, la motivación que falta, un ejemplo mejor) va en `> [!info] Ampliación (no está en el material)` y **siempre** se contrasta en el paso 5.

### 5. Contrastar con fuentes externas

El material puede tener erratas, estar desactualizado o simplificar de más, y tú puedes equivocarte al resumirlo. Contrasta los datos antes de dar los apuntes por buenos.

**Si está instalada la skill `contrastar`, sigue su modo "apuntes de aprender"**: es la versión completa de este paso (contrasta todas las afirmaciones, no una muestra). Lo de abajo es el mínimo cuando no está.

**Qué contrastar** (por orden de prioridad):
1. Todas las raíces (nivel 0) y las definiciones clave.
2. Fórmulas, cifras, fechas, nombres propios, unidades, artículos de leyes y clasificaciones.
3. Todas las `Ampliación` que hayas añadido tú.
4. Lo que se contradiga entre dos PDFs, o lo que te suene raro.

Si hay muchos conceptos, haz los grupos 1 a 4 completos y del resto una muestra. Anota en `01 <T> - Contraste.md` qué se ha quedado sin contrastar.

**Cómo contrastar:**
```bash
python3 -I <skill>/scripts/contrastar.py "<término>" --idiomas es,en [--completo] [--wikcionario]
```
Devuelve el título, la URL y el extracto de los mejores artículos de Wikipedia en español e inglés, y de Wikcionario si añades `--wikcionario`. Las fórmulas llegan en LaTeX. Usa `--completo` cuando el dato no esté en la introducción del artículo.

- Lanza varias búsquedas en paralelo (varias llamadas a `bash` en el mismo turno) o agrúpalas por tema.
- **Wikipedia no basta para todo**: si hay `researcher` o `web_search`, úsalos para lo especializado y busca la **fuente primaria**: el BOE o el texto consolidado para leyes españolas; la norma (ISO, UNE, IEEE) o la documentación oficial para lo técnico; el organismo oficial (INE, OMS, BCE…) para cifras; el artículo original o un manual de referencia para la ciencia. Sin esas herramientas, usa `curl` contra la web oficial si sabes la URL.
- Prefiere fuentes primarias y recientes. Una cifra sin fecha no vale para contrastar.

**Cómo registrarlo** en la sección `## Contraste` de cada nota, y en el frontmatter `contraste: verificado | discrepancia | matizado | sin-fuente`:

```markdown
## Contraste
> [!success] Verificado
> La definición coincide con [Wikipedia: Ley de Ohm](https://es.wikipedia.org/wiki/Ley_de_Ohm).

> [!danger] Discrepancia
> **El material dice** (p. 14): <cita literal>
> **La fuente externa dice**: <cita> ([fuente](url))
> **Valoración**: <cuál parece correcto y por qué: errata, dato antiguo, otra convención, simplificación…>
```

Reglas:
- **No cambies nunca en silencio lo que dice el material.** Puede ser lo que pidan en el examen. Deja las dos versiones a la vista y explica la diferencia.
- Si es una convención distinta (notación, signos, unidades) y no un error, usa `matizado` con un `> [!info]`.
- Si una `Ampliación` tuya no se confirma, **bórrala**.
- `01 <T> - Contraste.md` recoge un resumen (cuántos conceptos verificados, con discrepancia y sin contrastar), la lista de discrepancias con `[[enlaces]]` a cada nota, y las fuentes externas usadas.

### 6. Actualizar sin destruir

Si la carpeta `<T>/` ya tiene apuntes, o un concepto ya existe en otro tema: **lee cada nota antes de tocarla y fusiona**. No borres ni reescribas nunca `## Mis notas` ni el texto que se nota que ha escrito el usuario. No toques `estado`, `_<T> - Progreso.md` ni `Sesiones/`. Añade notas nuevas, amplía las que hay, actualiza el índice y vuelve a contrastar solo lo que haya cambiado.

### 7. Verificar y entregar

```bash
python3 -I <skill>/scripts/revisar_lectura.py "<salida>" --pdf "<valor pdf del manifiesto>"
python3 -I <skill>/scripts/revisar_enlaces.py "<sesión>"
```

- `revisar_lectura.py` comprueba que el registro de lectura de cada PDF cubre todas sus páginas. Si faltan páginas, **léelas** (no te limites a rellenar el registro), incorpora lo que haya a los apuntes y repite hasta que todo salga con ✓.
- `revisar_enlaces.py` se ejecuta sobre toda la carpeta de la sesión, porque los temas se enlazan entre sí. Corrige los enlaces rotos y conecta las huérfanas. Repite hasta que no quede ningún enlace roto.

Al usuario dale: de dónde ha sacado los PDFs y cuántas páginas ha leído (todas), cuántas notas y fuentes se han generado, las páginas con poco texto que no se han adaptado (si las hay), las verdades base, la ruta de estudio resumida, **el resultado del contraste (sobre todo las discrepancias)**, la carpeta donde están (`<T>/`), cómo abrirlo (Obsidian → "Abrir carpeta como vault" → **la carpeta de la sesión**, para que se vean todos los temas y sus enlaces, y la Vista de grafo; si estás en un servidor, mira la sección siguiente) y la oferta de empezar a estudiar.

### Si estás en un servidor por SSH

Obsidian no se ejecuta en el servidor: el usuario abre los apuntes en su ordenador. Si `$SSH_CONNECTION` está definida, o no hay entorno gráfico, al entregar los apuntes:

- Dale la **ruta absoluta** de la carpeta de la sesión en el servidor (`realpath`) y el usuario y host (`whoami`, `hostname -f`).
- Explícale cómo tenerlos en su ordenador, recomendando en este orden:
  1. **Syncthing** en el servidor y en el ordenador, sincronizando la carpeta de la sesión (excluyendo `pdf/` si no quiere los PDFs en el ordenador). Sincroniza en los dos sentidos, así que lo que escriba en `## Mis notas` desde Obsidian vuelve al servidor.
  2. **rsync** si solo quiere copiarlos: `rsync -avz --exclude pdf/ usuario@host:<sesión>/ ~/Obsidian/<materia>/`. Es en un sentido: si escribe notas en local, antes de la siguiente sesión tiene que devolverlas con `rsync -avz --update ~/Obsidian/<materia>/ usuario@host:<sesión>/`, o las cambiará encima de lo que tú escribas.
  3. **Git** si ya usa el plugin Obsidian Git.
- **Al empezar con unos apuntes que ya existen**, recuérdale en una línea que sincronice sus cambios locales antes (no lo preguntes ni esperes respuesta): si no, se trabajará sobre una versión antigua.
- Los PDFs también tienen que estar en el servidor: si no están, dile cómo subirlos a la subcarpeta `pdf/` de la sesión (`scp *.pdf usuario@host:<sesión>/pdf/` o `rsync -avz`).
- La generación de apuntes puede tardar mucho. Recomiéndale ejecutar Pi dentro de `tmux` para que no se corte si se cae la conexión. Las extensiones de subagentes de amosblomqvist/learn también necesitan tmux.

## Fase 2: estudiar

Los apuntes son el mapa; la sesión es donde se aprende. Sigue siempre la misma forma: **sondeo → plan → enseñanza**. Lo que cambia según el tema es el tamaño de cada fase, no su orden.

**Verifica antes de afirmar.** Si vas a decir algo que no está en los apuntes contrastados, o dudas aunque sea un poco, compruébalo primero (`contrastar.py`, `researcher` o `web_search`). Si la comprobación te corrige, dilo claramente. Si un concepto tiene `contraste: discrepancia`, explícale la discrepancia al usuario cuando lo enseñes.

### Hacer un quiz

Usa la herramienta `quiz` si existe (siempre con `correctAnswer` y `explanation`). Si no existe, pregunta en el chat con opciones A/B/C/D, espera la respuesta y corrige (✓ o ✗, cuál era la correcta y por qué). Una pregunta cada vez, adaptando la siguiente a la respuesta. Un "no lo sé" es un hueco que hay que enseñar, no un fallo.

Cómo construir las opciones para que no delaten la respuesta:
1. Cada opción es una afirmación desnuda, **sin justificación**. El razonamiento va en la explicación.
2. Escribe primero la opción correcta y después transfórmala en cada distractor: lo que diría alguien con una confusión concreta y real, con la misma estructura, longitud y registro.
3. Los distractores tienen que tentar, pero ser inequívocamente falsos. Nada de negritas solo en una opción.
4. Si sin saber la materia se adivina cuál es la correcta, rehaz la pregunta.

Las preguntas sin respuesta correcta (objetivo, ritmo, preferencias) se hacen con `ask_user_question`, o en el chat si no existe.

### Fase A: sondeo (nunca te la saltes)

- **Su fuente**: la del paso 0. Si ese PDF aún no tiene apuntes (`con_apuntes: false`), haz antes la fase 1 con él.
- **Su objetivo**: dedúcelo de lo que haya dicho, de `_<T> - Progreso.md` y de la última sesión en `<T>/Sesiones/`. Solo si no se puede deducir, haz **una** pregunta abierta (¿examen, cuándo y de qué tipo, o entender a fondo? ¿qué tema?).
- **Su nivel** (quiz): por cada línea de prerrequisitos del objetivo, busca el **borde**: algo que acierta (suelo) y algo que falla (techo). Si acierta todo, sube mucho la dificultad. Si falla una, pregunta alrededor para distinguir despiste, hueco o concepción errónea. Las concepciones erróneas se desmontan, no se tapan.
- Lee `_<T> - Progreso.md` y el `estado` de las notas para no volver a sondear lo que ya está dominado y reciente.

### Fase B: plan (piensa aquí)

Según su borde y su objetivo, saca del grafo el subgrafo necesario. Preséntalo en el chat:
1. **El enfoque** en unas pocas frases: qué, en qué orden y por qué.
2. **Un mapa mermaid pequeño**, con las raíces arriba y el objetivo abajo.

Antes, pon a prueba las raíces: ¿cada una es incondicional *para él* o es un teorema disfrazado? **Espera a que dé el visto bueno** antes de empezar a enseñar.

### Fase C: enseñar nodo a nodo

Para **cada nodo**, sea una raíz o un paso derivado:
1. **Motivar**: por qué lo necesitamos ahora.
2. **Establecer**: si es una raíz, enúnciala tal cual. Si es un paso derivado, constrúyelo desde lo ya establecido: en modo **socrático** (plantea el problema y deja que lo intente, con quiz si tiene respuesta correcta) o **expositivo** (cuéntale tú el descubrimiento motivado) cuando el salto sea grande o tenga poca energía.
3. **Conectar**: haz explícita la arista con lo que ya tiene.
4. **Comprobar**: un quiz corto. Si falla, el nodo no está firme: arréglalo antes de seguir.

Apóyate en la nota del concepto, pero explica de forma activa; no le pegues la nota. Si la explicación de la sesión mejora la de la nota, propón actualizarla.

### Registrar el progreso

Al cerrar cada nodo, y siempre antes de terminar:
- En el frontmatter de la nota: `estado` (`nuevo` → `aprendiendo` → `dominado`), `ultimo_repaso: AAAA-MM-DD` y `proximo_repaso: AAAA-MM-DD`.
- **Repaso espaciado**: intervalos de 1, 3, 7, 14, 30 y 60 días. Un acierto avanza al siguiente intervalo; un fallo lo devuelve a 1 día y el estado a `aprendiendo`.
- En `_<T> - Progreso.md`: una tabla `| Concepto | Estado | Último repaso | Próximo repaso | Notas |`.
- En `<T>/Sesiones/<T> AAAA-MM-DD.md`: qué se vio (con `[[enlaces]]`), el mapa del plan, los quizzes con el resultado, las concepciones erróneas detectadas y qué queda pendiente.

### Modo repaso

Con `repaso`: busca las notas con `proximo_repaso` igual o anterior a hoy, y las que estén en `aprendiendo`. Haz un quiz de cada una, intercalando temas y empezando por el nivel más bajo. Actualiza los intervalos. Si algo falla, vuelve a enseñar ese nodo y comprueba también sus dependencias, porque el fallo puede estar más abajo.
