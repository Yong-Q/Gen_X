-- Source documents live in docs/. Repository links remain useful after PDF export.
-- Each source's top-level title starts a chapter on a fresh page, including
-- the first title after the automatically generated table of contents.
function Header(header)
  if FORMAT:match('latex') and header.level == 1 then
    return {pandoc.RawBlock('latex', '\\clearpage'), header}
  end
  return header
end

function Link(link)
  local target = link.target
  if target:match('^#') or target:match('^[%a][%w+.-]*:') then
    return link
  end
  local parts = {'docs'}
  for part in target:gmatch('[^/]+') do
    if part == '..' then
      table.remove(parts)
    elseif part ~= '.' then
      table.insert(parts, part)
    end
  end
  link.target = 'https://github.com/Yong-Q/Gen_X/blob/main/' .. table.concat(parts, '/')
  return link
end

-- Pandoc's zero-width pipe-table columns become unwrapped l/r columns in LaTeX.
-- Preserve legibility in dense workflow figures. HTML uses SVG; PDF uses the
-- vector counterpart on a dedicated portrait page with a page number.
function Para(block)
  if FORMAT:match('latex') and #block.content == 1 and block.content[1].t == 'Image' then
    local source = block.content[1].src
    if source:match('^figures/research_v2/[%w_]+%.svg$') then
      local root = os.getenv('GENX_PDF_REPO_ROOT') or '.'
      local resolved = root .. '/docs/' .. source:gsub('%.svg$', '.pdf')
      return pandoc.RawBlock('latex', '\\begin{figure}[p]\\centering\\includegraphics[width=\\linewidth,height=.99\\textheight,keepaspectratio]{' .. resolved .. '}\\end{figure}')
    end
  end
  return block
end

-- Give them actual widths so Chinese prose and repository names stay on the page.
function Table(tbl)
  local count = #tbl.colspecs
  if count > 0 then
    for i = 1, count do
      tbl.colspecs[i][2] = 1 / count
    end
  end
  return tbl
end
