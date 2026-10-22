-- Source documents live in docs/. Repository links remain useful after PDF export.
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
