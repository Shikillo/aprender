---
name: contrastar
description: Verifica afirmaciones contra Wikipedia y fuentes primarias (BOE, normas, organismos oficiales, artículos), afirmación por afirmación y citando cada fuente. Comprueba definiciones, fórmulas, cifras, fechas, nombres y leyes de un PDF, de unos apuntes .md o Obsidian (también los que genera la skill aprender) o de un texto. Marca cada afirmación como verificada, discrepante, matizada o sin fuente, y nunca cambia el original en silencio. Úsala cuando el usuario quiera contrastar, verificar o comprobar datos, buscar erratas o errores, o saber si un temario o unos apuntes son fiables o están actualizados.
compatibility: Pi en Linux (también por SSH) o macOS. Necesita python3 con pypdf y acceso a internet. Opcional pero recomendado, el agente researcher o las herramientas web_search/web_fetch (por ejemplo, de github.com/amosblomqvist/learn) para fuentes primarias.
---

# Contrastar

Comprueba si lo que dice un material es cierto y está actualizado, **afirmación por afirmación**, contra fuentes externas, y deja por escrito el resultado con sus fuentes.

Uso: `/skill:contrastar [PDF | nota.md | carpeta de apuntes | texto]`

**Dónde se escribe**: igual que `aprender`, en **una carpeta por PDF** con el nombre del PDF, dentro de la carpeta donde se ha abierto Pi (`<sesión>`). Si abres Pi en `/Estudios` y contrastas `/Estudios/pdf/Tema1.pdf`, el informe va a `/Estudios/Tema1/`. El extractor da esa ruta en el campo `salida` (en adelante `<T>` es su nombre). Si `aprender` ya creó esa carpeta, se comparte.

Los scripts están en `scripts/`, dentro del directorio de esta skill (Pi te dice dónde está). En los comandos, `<skill>` es esa ruta. Ejecútalos siempre con `python3 -I`. Habla con el usuario en su idioma; escribe el informe en el idioma del material.

## Reglas que no se negocian

- **Leer todo.** Se lee cada página o cada nota completa. Nada de suponer lo que dice una parte sin haberla leído.
- **Contrastar todo lo verificable.** Cada afirmación verificable que encuentres se contrasta, no una muestra. Si el volumen obliga a parar, dilo en el informe con la cifra exacta de lo que falta, nunca en silencio.
- **No tocar el original.** Nunca se edita un PDF. En las notas solo se **añade** el resultado del contraste; el texto original no se reescribe.
- **Ser honesto.** Una afirmación solo es "verificada" si una fuente externa concreta dice lo mismo, y se cita esa fuente con su URL. Que "te suene correcto" no es una verificación. Si no encuentras fuente, es `sin-fuente`.
- **Pregunta lo mínimo.** Lo único que se pregunta es qué contrastar (paso 0). Todo lo demás se hace sin preguntar.

## Paso 0: qué contrastar

1. **Si se ha indicado** al invocarla (una ruta a un PDF o a un `.md`, una carpeta de apuntes, un nombre o un trozo del nombre, o texto pegado), úsalo sin preguntar.
2. **Si no**, mira qué hay en el directorio actual:
   ```bash
   python3 -I <skill>/scripts/extraer_pdfs.py --listar
   find . -mindepth 2 -maxdepth 2 -name "00 * - Índice.md" -not -path "*/.*"   # temas con apuntes de aprender
   find . -maxdepth 2 -name "*.md" -not -path "*/.*" | head -50
   ```
   Pregunta qué contrastar, con `ask_user_question` si existe o en el chat, mediante una lista numerada que incluya:
   - cada PDF, con sus páginas;
   - cada carpeta de tema con apuntes de `aprender` (las que tienen `00 <T> - Índice.md`), como una opción por tema;
   - las notas `.md` sueltas o sus carpetas.

   Si solo hay una opción, úsala y di cuál es. Si no hay nada, pide que pegue el texto o indique una ruta.

## Paso 1: leer y extraer las afirmaciones

**PDF:**
```bash
cd "<sesión>" && python3 -I <skill>/scripts/extraer_pdfs.py --pdf "<elegido>"
```
(o pasa la ruta del PDF como primer argumento; aunque esté fuera, la carpeta `<T>/` se crea en la de la sesión). Parte el PDF en tramos de 10 páginas: lee **todos** los tramos, enteros y en orden. Después de cada tramo, añade sus páginas al **registro de lectura** del informe (`- p. N: …`), incluidas las que no tengan nada verificable ("p. 1: portada").

**Notas .md o carpeta de apuntes:** lee cada nota entera. En unos apuntes de `aprender`, lo verificable está sobre todo en "Qué es", "Ejemplo" y los callouts `Ampliación`, y la página original está en `## Fuentes`.

**Texto pegado:** trabaja directamente sobre él y responde en el chat (paso 4).

**Qué es una afirmación verificable**: definiciones, fórmulas y unidades, cifras y estadísticas, fechas, nombres propios y autorías, artículos y números de leyes o normas, clasificaciones y enumeraciones ("los tres tipos de…"), relaciones causa-efecto que se presentan como hechos, y afirmaciones universales ("siempre", "ningún", "todos").

**No son verificables**: opiniones, consejos, ejemplos inventados como ilustración, ni la estructura del propio documento. No las cuentes.

Para cada afirmación anota: la cita literal, dónde está (página o nota y sección) y qué tipo de dato es.

**Mucho material** (más de unos 150 páginas o unas 40 notas) y hay subagentes: reparte por tramos o grupos de notas, en paralelo. Cada subagente lee **toda** su parte y devuelve el registro de lectura sin huecos y la lista de afirmaciones. Dale las rutas, estas reglas y el formato exacto, porque no ve esta conversación.

## Paso 2: contrastar

Para cada afirmación, busca **al menos una fuente externa** que la confirme o la contradiga.

**Wikipedia** (siempre disponible, sin instalar nada):
```bash
python3 -I <skill>/scripts/contrastar.py "<término>" --idiomas es,en [--completo] [--wikcionario]
```
Devuelve el título, la URL y el extracto de los mejores artículos en español e inglés, con las fórmulas en LaTeX. Usa `--completo` si el dato no está en la introducción y `--wikcionario` para definiciones de términos. Lanza varias búsquedas en paralelo (varias llamadas a `bash` en el mismo turno).

**Fuentes primarias**, con `researcher`, `web_search` o `web_fetch` si existen, o con `curl` si conoces la URL oficial:

| Tipo de dato | Fuente preferida |
|---|---|
| Leyes y normativa española | BOE, en la versión **consolidada** y vigente (boe.es) |
| Normativa europea | EUR-Lex |
| Normas técnicas | ISO, UNE, IEEE, IETF (RFC), W3C, documentación oficial del producto |
| Cifras y estadísticas | El organismo que las publica (INE, Eurostat, OMS, BCE, Banco de España…), con fecha |
| Ciencia | El artículo original, un manual de referencia o una sociedad científica |
| Definiciones de términos | RAE (dle.rae.es) y diccionarios técnicos |
| Historia, biografías y conceptos generales | Wikipedia, revisando sus referencias si el dato es dudoso |

Criterios:
- Lo primario pesa más que Wikipedia, y Wikipedia más que blogs o foros. No uses como fuente páginas de relleno SEO ni contenido generado sin referencias.
- **Vigencia**: las leyes cambian, las cifras caducan y las normas se revisan. Comprueba siempre la versión vigente o el dato más reciente, con su fecha. Que el material use una versión antigua es una discrepancia por **desactualización**, y hay que decirlo así.
- Si Wikipedia en español y en inglés no coinciden, o la fuente es dudosa, busca una segunda fuente independiente antes de concluir.
- Antes de marcar una discrepancia, comprueba que no es una diferencia de **convención** (notación, signos, unidades, redondeo, definición alternativa aceptada). Si lo es, va como `matizado`.

## Paso 3: clasificar

| Estado | Cuándo |
|---|---|
| `verificado` | Una fuente fiable dice lo mismo (se cita) |
| `matizado` | Es correcto con matices: simplificación aceptable, otra convención o una excepción relevante que el material omite |
| `discrepancia` | Una fuente fiable dice otra cosa: errata, error o dato desactualizado |
| `sin-fuente` | No se ha encontrado fuente que lo confirme ni lo contradiga |

En cada `discrepancia` explica **cuál es el problema** (errata, error de concepto, dato antiguo, confusión con otro concepto), **qué parece correcto y por qué**, y si hay riesgo de examen ("el temario dice X; si el examen sigue el temario, pueden esperar X").

## Paso 4: escribir el resultado

### Si es un PDF: un informe en `<sesión>/<T>/Contraste - <T>.md`

El nombre lleva `<T>` para que no se repita entre temas, porque Obsidian enlaza por nombre.

```markdown
---
tipo: contraste
pdf: <el valor "pdf" del manifiesto, tal cual>
paginas: 48
fecha: AAAA-MM-DD
verificado: 0
matizado: 0
discrepancia: 0
sin-fuente: 0
---
# Contraste - <T>

## Resumen
<2–4 líneas: cuántas afirmaciones, fiabilidad general, los problemas más graves>

## Discrepancias
> [!danger] p. 14: <tema>
> **El material dice**: <cita literal>
> **La fuente dice**: <cita> ([fuente](url), fecha si aplica)
> **Valoración**: <qué tipo de problema es, qué es lo correcto y por qué, riesgo de examen>

## Matices
> [!info] p. 20: <tema>
> <qué matiz falta y su fuente>

## Verificado
| Pág. | Afirmación | Fuente |
|---|---|---|
| 3 | <resumen corto> | [Wikipedia: X](url) |

## Sin fuente
- p. 31: <afirmación>: <dónde se ha buscado>

## Registro de lectura
- p. 1: portada
- p. 2–3: <qué hay>; 4 afirmaciones

## Fuentes consultadas
- [Título](url): <para qué se ha usado>
```

Después comprueba que se ha leído todo:
```bash
python3 -I <skill>/scripts/revisar_lectura.py "<salida>" --pdf "<valor pdf del manifiesto>"
```
Si faltan páginas, **léelas** y contrástalas; no rellenes el registro sin leerlas. Repite hasta que salga ✓.

### Si son apuntes de la skill `aprender` (notas con `tipo: concepto`)

Mismo formato que su paso 5:
- En cada nota, rellena `## Contraste` con callouts (`> [!success] Verificado`, `> [!info]` si está matizado, `> [!danger] Discrepancia` con "El material dice / La fuente externa dice / Valoración") y pon en el frontmatter `contraste: verificado | matizado | discrepancia | sin-fuente`. El estado de la nota es el peor de sus afirmaciones.
- Si un callout `Ampliación (no está en el material)` no se confirma, bórralo: lo añadió la IA, no el material.
- No toques `## Mis notas`, `estado`, `_<T> - Progreso.md` ni `Sesiones/`.
- Actualiza `01 <T> - Contraste.md` (en la carpeta del tema) con el resumen, las discrepancias enlazadas con `[[nota]]` y las fuentes consultadas.

### Si son otras notas .md

Escribe un informe aparte, `Contraste - <nombre>.md`, junto a la nota o en la raíz de la carpeta. Usa el mismo formato que el de los PDF, cambiando "p. N" por `[[nota#sección]]` y sin registro de lectura de páginas (en su lugar, la lista de notas leídas). Solo anota dentro de las notas originales (una sección `## Contraste` al final) si el usuario lo pide.

### Si es texto pegado

Responde en el chat con el mismo esquema (discrepancias, matices, verificado y sin fuente), con los enlaces a las fuentes. No crees ficheros salvo que te lo pida.

## Paso 5: entregar

Al usuario dale:
- qué se ha leído (páginas o notas, todas);
- cuántas afirmaciones hay de cada estado;
- **las discrepancias**, una línea cada una con su página y lo que parece correcto;
- dónde está el informe.

Si estás por SSH (`$SSH_CONNECTION`), da la ruta absoluta del informe para que pueda traérselo a su ordenador.
