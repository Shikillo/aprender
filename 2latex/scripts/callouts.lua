-- Filtro de pandoc para 2latex: convierte los divs ::: callout-<tipo> en \begin{callout}{tipo}{título}.
-- md2latex.py genera esos divs a partir de los callouts de Obsidian (> [!tipo] Título).
-- El título va como primer párrafo, en un span [Título]{.callout-titulo}, para que pueda llevar
-- negritas, fórmulas, etc. y pandoc lo convierta bien a LaTeX.

local function a_latex(inlines)
  local texto = pandoc.write(pandoc.Pandoc({ pandoc.Plain(inlines) }), "latex")
  return (texto:gsub("%s+$", ""))
end

function Div(el)
  local tipo
  for _, clase in ipairs(el.classes) do
    tipo = tipo or clase:match("^callout%-(.+)$")
  end
  if not tipo then
    return nil
  end

  local titulo = ""
  local primero = el.content[1]
  if primero and (primero.t == "Para" or primero.t == "Plain")
      and primero.content[1] and primero.content[1].t == "Span"
      and primero.content[1].classes:includes("callout-titulo") then
    titulo = a_latex(primero.content[1].content)
    table.remove(el.content, 1)
  end

  local bloques = { pandoc.RawBlock("latex", "\\begin{callout}{" .. tipo .. "}{" .. titulo .. "}") }
  for _, b in ipairs(el.content) do
    table.insert(bloques, b)
  end
  table.insert(bloques, pandoc.RawBlock("latex", "\\end{callout}"))
  return bloques
end
