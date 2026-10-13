---
name: jardin
description: Deja una carpeta de notas de Obsidian lista para publicarse con el plugin Digital Garden. Revisa todas las notas .md y les añade dg-publish true donde falte, respetando las que estén en false. Crea o completa index.md como portada (dg-home) con enlaces a todas las asignaturas o temas, sin borrar lo que ya tenga, y avisa de los problemas. Úsala cuando el usuario quiera publicar sus notas o su vault, preparar o revisar el jardín digital, marcar notas para publicar o actualizar el index con las asignaturas.
compatibility: Pi en Linux (también por SSH) o macOS. Solo necesita python3.
---

# Jardín digital

Prepara la carpeta donde se ha abierto Pi (`<sesión>`), o la que indique el usuario, para publicarla con el plugin Digital Garden de Obsidian.

Uso: `/skill:jardin [carpeta] [simular]`

El script está en `scripts/`, dentro del directorio de esta skill (Pi te dice dónde está). En los comandos, `<skill>` es esa ruta.

**No preguntes nada.** La carpeta es la actual salvo que se indique otra.

**No imprimas las notas en el terminal.** Créalas y sigue: el usuario las lee en Obsidian.
- Crea los ficheros con la herramienta `write` y modifícalos con `edit`. **Nunca** con `cat <<EOF`, `echo`, `printf` ni `tee` en `bash`: el comando entero, con la nota dentro, sale en el terminal.
- **Nunca** copies el contenido de una nota o informe en tu respuesta, ni entero, ni a trozos, ni como "vista previa" o "así ha quedado".
- No uses `cat` para enseñar un fichero. Para leerlo tú, usa `read`.
- Mientras trabajas, como mucho una línea de progreso por paso ("Tema1: 12/30 notas escritas"). Al terminar, solo el resumen que pide el último paso, con nombres y rutas de fichero, no con su contenido.

## Paso 1: revisar y marcar

Con `simular`, ejecuta solo con `--simular`, que no escribe nada. Después explica qué cambiaría y termina. Sin `simular`, ejecuta directamente:

```bash
python3 -I <skill>/scripts/preparar_jardin.py "<carpeta>" [--simular]
```

Qué hace el script:
- **Todas las notas `.md`** (salvo las de carpetas ocultas como `.fuentes/`, `.latex/` u `.obsidian/`) llevan `dg-publish: true`. Si no tienen frontmatter, se lo añade sin tocar el resto de la nota.
- **Respeta `dg-publish: false`**: es el usuario diciendo que esa nota no se publica. Nunca lo cambies a `true`, ni con el script ni a mano.
- **`index.md`** en la raíz es la portada: `dg-publish: true` y `dg-home: true`. Si no existe, lo crea. En su sección `## Asignaturas` añade un enlace a cada carpeta con índice de tema (`<T>/00 <T> - Índice.md`) que falte. **Nunca borra nada** de lo que ya haya.
- Si existe el antiguo `00 Índice general.md` y no hay `index.md`, lo renombra y actualiza los enlaces que apuntaban a él.
- Si otra nota ya es la portada (`dg-home: true`), **no** marca `index.md` como portada (el plugin solo admite una) y lo avisa.

## Paso 2: completar el index

Para cada tema de `asignaturas_añadidas` el script deja una línea `- [[00 <T> - Índice|<T>]]` sin descripción:
1. Lee `<T>/00 <T> - Índice.md` (el párrafo de "de qué va").
2. Añade al final de esa línea de `index.md` una descripción de una frase: `- [[00 Tema1 - Índice|Tema1]]: circuitos eléctricos básicos y ley de Ohm`.

No toques nada más del index.

## Paso 3: avisos que hay que explicar

| Aviso | Qué decirle al usuario |
|---|---|
| Otra nota ya es la portada | Cuál es, y que si quiere que lo sea `index.md` tiene que quitarle `dg-home` a la otra |
| Carpetas con notas pero sin índice | No se han enlazado en el index porque no tienen `00 <T> - Índice.md`. Se publican igual, pero no se llega a ellas desde la portada. Puede crear su índice con `/skill:aprender`, o enlazarlas a mano en `index.md` |
| `no_publicadas_por_decision_del_usuario` | Lista de notas con `dg-publish: false` que **no** se publicarán |
| Enlaces a notas no publicadas | Si alguna nota publicada enlaza a una de esas, el enlace saldrá roto en la web. Búscalo y avisa: `grep -rl "\[\[<nombre>" "<carpeta>" --include=*.md` |

## Paso 4: entregar

Resume en pocas líneas:
- cuántas notas se han marcado ahora y cuántas ya lo estaban;
- si `index.md` se ha creado o actualizado, y qué asignaturas se han añadido;
- los avisos del paso 3.

Recuérdale que para publicar abra Obsidian en esa carpeta, pulse Ctrl/Cmd + P, escriba «Digital Garden» y abra el centro de publicación del plugin, donde verá las notas pendientes de publicar.

Si estás por SSH (`$SSH_CONNECTION`), los cambios están en el servidor: tiene que sincronizar la carpeta (Syncthing o rsync) antes de publicar desde su Obsidian.
