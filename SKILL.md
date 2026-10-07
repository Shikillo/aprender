---
name: aprender
description: Convierte una carpeta de PDFs (temarios, apuntes, libros, diapositivas) en un vault de apuntes .md enlazados al estilo Obsidian ([[wikilinks]], mapa de dependencias, preguntas de autoevaluación), contrasta los datos con Wikipedia y otras fuentes externas, y después enseña la materia con sesiones guiadas (sondeo, plan, enseñanza nodo a nodo, quiz y repaso espaciado). Úsala cuando el usuario quiera estudiar o aprender una materia a partir de PDFs, hacer apuntes o resúmenes enlazados, verificar unos apuntes, preparar un examen o repasar apuntes generados antes.
compatibility: Pi en Linux (también por SSH) o macOS. Necesita python3 con pypdf y acceso a internet para el contraste. Opcional pero recomendado, las extensiones quiz y ask_user_question y el agente researcher de github.com/amosblomqvist/learn. Opcional, pdftoppm (poppler) para ver páginas escaneadas.
---

# Aprender una materia a partir de PDFs

Dos fases, que pueden hacerse por separado:

1. **Apuntes**: leer los PDFs, construir un vault de notas atómicas enlazadas y **contrastar** los datos con fuentes externas.
2. **Estudiar**: enseñar la materia usando esos apuntes como mapa, y registrar el progreso.

Uso: `/skill:aprender <carpeta> [apuntes | contrastar | estudiar | repaso]`
- `apuntes`, o una carpeta sin apuntes todavía → fase 1. Al terminar, ofrece empezar la fase 2.
- `contrastar` → solo el paso 5 de la fase 1, sobre unos apuntes que ya existen.
- `estudiar` / `repaso`, o una carpeta que ya tiene `apuntes/` → fase 2. Si hay PDFs nuevos o modificados, ofrece actualizar los apuntes primero.
- Sin ruta: usa el directorio actual si contiene PDFs; si no, pregunta.

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
| Ver páginas escaneadas o diagramas | `read` sobre las imágenes que genera el extractor | Pide al usuario que instale poppler (`doas apk add poppler-utils` en Alpine; `sudo apt install poppler-utils` en Debian/Ubuntu; `brew install poppler` en macOS) |

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
python3 -I <skill>/scripts/extraer_pdfs.py "<carpeta>" "<carpeta>/apuntes/.fuentes"
```

Recorre la carpeta de forma recursiva (también las subcarpetas de PDFs), guarda un `.md` por PDF con cabeceras `## Página N` y devuelve un manifiesto JSON. Lo que ya está en caché no se vuelve a extraer.

- `paginas_poco_texto` señala páginas escaneadas, con diagramas o con fórmulas. Sus imágenes van a `.fuentes/<pdf>.img/` (lista `imagenes` del manifiesto): ábrelas con `read` y transcribe lo que veas. No inventes lo que no has podido ver; si no hay imágenes, díselo al usuario y continúa con el resto.
- Si falta `pypdf`, pide al usuario que lo instale con el gestor del sistema: `doas apk add py3-pypdf` en Alpine o `sudo apt install python3-pypdf` en Debian/Ubuntu. Usa `python3 -m pip install --user pypdf` solo si no hay paquete, porque pip suele dar el error `externally-managed-environment`.
- La carpeta `.fuentes/` empieza por punto, así que Obsidian no la muestra.

### 2. Leer e inventariar conceptos

Lee **todo** el material, no solo el principio. Para cada fuente, saca un inventario:
- conceptos, con su definición literal y las páginas donde aparecen;
- de qué otros conceptos depende cada uno;
- ejemplos, fórmulas, procedimientos, fechas, cifras y errores típicos que señale el material;
- la estructura del documento (temas y capítulos).

**Mucho material** (más de unos 150 páginas, o muchos PDFs) y hay subagentes: lanza uno por PDF o bloque de capítulos, en paralelo. Cada uno lee su `.md` de `.fuentes/` y devuelve el inventario con este formato:
`concepto | aliases | definición (cita) | páginas | depende de | datos verificables | ejemplos | errores típicos`.
Recuerda que los subagentes no ven esta conversación: dales la ruta del fichero y el formato exacto.

### 3. Unificar y construir el grafo

- **Quita duplicados**: el mismo concepto con nombres distintos es **una sola nota**; los otros nombres van a `aliases`. Si dos PDFs se contradicen, apúntalo para el paso 5.
- **Granularidad**: una nota por concepto que merezca explicarse por sí solo. Ni una por cada término menor, ni un tema entero en una nota.
- **Ordena por dependencias**: las raíces son verdades incondicionales y definiciones. Pon a prueba cada raíz: ¿se acepta tal cual, o se deduce de algo más simple? Si se deduce, bájala y añade el nodo de debajo. El orden topológico es la **ruta de estudio**.
- `nivel`: 0 para las raíces; para el resto, 1 más que el mayor nivel de sus dependencias.

### 4. Escribir el vault

Por defecto, en `<carpeta>/apuntes/` (si el usuario indica su vault de Obsidian, escribe allí):

```
apuntes/
├── 00 Índice.md            ← MOC: mapa, ruta de estudio, índice por temas
├── 01 Contraste.md         ← informe de verificación (paso 5)
├── _Progreso.md            ← lo rellena la fase 2
├── Fuentes/
│   └── <Nombre del PDF>.md ← resumen del documento y qué conceptos salen de cada capítulo
├── Conceptos/
│   └── <Concepto>.md
├── Sesiones/
│   └── AAAA-MM-DD.md       ← registro de cada sesión de estudio
└── .fuentes/               ← texto extraído e imágenes (caché, oculto en Obsidian)
```

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
fuentes: ["[[<Nombre del PDF>]]"]
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
- [[<Nombre del PDF>]], p. 12–14

## Mis notas
```

**`00 Índice.md`**: de qué va la materia y su idea central; las **verdades base** (nivel 0) con su frase; el **mapa de dependencias** en mermaid (`graph TD`, raíces arriba; si hay más de unos 25 nodos, un mapa por tema y otro global de temas); la **ruta de estudio** numerada en orden topológico; un índice por tema; y enlaces a todas las fuentes y a `[[01 Contraste]]`.

**Nota de fuente**: `tipo: fuente` y la ruta del PDF; un resumen de 5 a 10 líneas; y, capítulo a capítulo, qué conceptos introduce (`[[enlaces]]`) con sus páginas.

**Fidelidad**: lo que pongas en "Qué es", "Ejemplo" y "Fuentes" tiene que salir de los PDFs, citando la página. Lo que añadas tú (una intuición, la motivación que falta, un ejemplo mejor) va en `> [!info] Ampliación (no está en el material)` y **siempre** se contrasta en el paso 5.

### 5. Contrastar con fuentes externas

El material puede tener erratas, estar desactualizado o simplificar de más, y tú puedes equivocarte al resumirlo. Contrasta los datos antes de dar los apuntes por buenos.

**Qué contrastar** (por orden de prioridad):
1. Todas las raíces (nivel 0) y las definiciones clave.
2. Fórmulas, cifras, fechas, nombres propios, unidades, artículos de leyes y clasificaciones.
3. Todas las `Ampliación` que hayas añadido tú.
4. Lo que se contradiga entre dos PDFs, o lo que te suene raro.

Si hay muchos conceptos, haz los grupos 1 a 4 completos y del resto una muestra. Anota en `01 Contraste.md` qué se ha quedado sin contrastar.

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
- `01 Contraste.md` recoge un resumen (cuántos conceptos verificados, con discrepancia y sin contrastar), la lista de discrepancias con `[[enlaces]]` a cada nota, y las fuentes externas usadas.

### 6. Actualizar sin destruir

Si `apuntes/` ya existe: **lee cada nota antes de tocarla y fusiona**. No borres ni reescribas nunca `## Mis notas` ni el texto que se nota que ha escrito el usuario. No toques `estado`, `_Progreso.md` ni `Sesiones/`. Añade notas nuevas, amplía las que hay, actualiza el índice y vuelve a contrastar solo lo que haya cambiado.

### 7. Verificar y entregar

```bash
python3 -I <skill>/scripts/revisar_enlaces.py "<carpeta>/apuntes"
```

Corrige los enlaces rotos y conecta las huérfanas. Repite hasta que no quede ningún enlace roto.

Al usuario dale: cuántas notas y fuentes se han generado, las verdades base, la ruta de estudio resumida, **el resultado del contraste (sobre todo las discrepancias)**, cómo abrirlo (Obsidian → "Abrir carpeta como vault" → `apuntes/`, y la Vista de grafo; si estás en un servidor, mira la sección siguiente) y la oferta de empezar a estudiar.

### Si estás en un servidor por SSH

Obsidian no se ejecuta en el servidor: el usuario abre los apuntes en su ordenador. Si `$SSH_CONNECTION` está definida, o no hay entorno gráfico, al entregar los apuntes:

- Dale la **ruta absoluta** de `apuntes/` en el servidor (`realpath`) y el usuario y host (`whoami`, `hostname -f`).
- Explícale cómo tenerlos en su ordenador, recomendando en este orden:
  1. **Syncthing** en el servidor y en el ordenador, sincronizando la carpeta `apuntes/`. Sincroniza en los dos sentidos, así que lo que escriba en `## Mis notas` desde Obsidian vuelve al servidor.
  2. **rsync** si solo quiere copiarlos: `rsync -avz usuario@host:<ruta>/apuntes/ ~/Obsidian/<materia>/`. Es en un sentido: si escribe notas en local, antes de la siguiente sesión tiene que devolverlas con `rsync -avz --update ~/Obsidian/<materia>/ usuario@host:<ruta>/apuntes/`, o las cambiará encima de lo que tú escribas.
  3. **Git** si ya usa el plugin Obsidian Git.
- **Antes de tocar unos apuntes que ya existen**, pregunta si ha sincronizado sus cambios locales. Si no, podrías trabajar sobre una versión antigua.
- Los PDFs también tienen que estar en el servidor: si no están, dile cómo subirlos (`scp -r <carpeta> usuario@host:<ruta>` o `rsync -avz`).
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

- **Su objetivo** (pregunta abierta): ¿examen (cuándo y de qué tipo)? ¿entender a fondo? ¿qué tema? Concreta hasta que esté claro.
- **Su nivel** (quiz): por cada línea de prerrequisitos del objetivo, busca el **borde**: algo que acierta (suelo) y algo que falla (techo). Si acierta todo, sube mucho la dificultad. Si falla una, pregunta alrededor para distinguir despiste, hueco o concepción errónea. Las concepciones erróneas se desmontan, no se tapan.
- Lee `_Progreso.md` y el `estado` de las notas para no volver a sondear lo que ya está dominado y reciente.

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
- En `_Progreso.md`: una tabla `| Concepto | Estado | Último repaso | Próximo repaso | Notas |`.
- En `Sesiones/AAAA-MM-DD.md`: qué se vio (con `[[enlaces]]`), el mapa del plan, los quizzes con el resultado, las concepciones erróneas detectadas y qué queda pendiente.

### Modo repaso

Con `repaso`: busca las notas con `proximo_repaso` igual o anterior a hoy, y las que estén en `aprendiendo`. Haz un quiz de cada una, intercalando temas y empezando por el nivel más bajo. Actualiza los intervalos. Si algo falla, vuelve a enseñar ese nodo y comprueba también sus dependencias, porque el fallo puede estar más abajo.
