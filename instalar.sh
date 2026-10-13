#!/bin/sh
# Instala las skills de este repo en Claude Code.
#
#   ./instalar.sh                 enlaza cada skill en ~/.claude/skills/ (todas tus carpetas)
#   ./instalar.sh .claude/skills  enlaza en otra carpeta (p. ej. solo para un proyecto)
#   ./instalar.sh --quitar        borra los enlaces que creó este script
#
# Pi no lo necesita: con el repo clonado en ~/.agents/skills/estudio, Pi encuentra las skills
# en las subcarpetas. Claude Code solo mira las subcarpetas directas de ~/.claude/skills/, así
# que aquí se crea un enlace por skill. Son enlaces, no copias: con `git pull` en el repo, Pi y
# Claude Code usan a la vez la versión nueva.
set -e

REPO=$(cd "$(dirname "$0")" && pwd)
QUITAR=0
DESTINO="$HOME/.claude/skills"
for arg in "$@"; do
  case "$arg" in
    --quitar) QUITAR=1 ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) DESTINO="$arg" ;;
  esac
done

mkdir -p "$DESTINO"
for dir in "$REPO"/*/; do
  dir=${dir%/}
  [ -f "$dir/SKILL.md" ] || continue
  nombre=$(basename "$dir")
  enlace="$DESTINO/$nombre"
  if [ "$QUITAR" = 1 ]; then
    if [ -L "$enlace" ] && [ "$(readlink "$enlace")" = "$dir" ]; then
      rm "$enlace" && echo "quitado:     $enlace"
    fi
    continue
  fi
  if [ -L "$enlace" ]; then
    ln -sfn "$dir" "$enlace" && echo "actualizado: $enlace -> $dir"
  elif [ -e "$enlace" ]; then
    echo "AVISO: $enlace ya existe y no es un enlace; no lo toco. Bórralo o renómbralo y vuelve a ejecutar."
  else
    ln -s "$dir" "$enlace" && echo "instalado:   $enlace -> $dir"
  fi
done
[ "$QUITAR" = 1 ] || echo "Listo. Abre una sesión nueva de Claude Code y escribe / para ver las skills."
