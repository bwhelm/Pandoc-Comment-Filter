--[[
Pandoc filter to extend pandoc's markdown to incorporate comment features and
other things I find useful. With `draft: true` in the YAML header, comments and
margin notes are displayed in red, and text that is highlighted or flagged with
`fixme` is marked up in the output. With `draft: false` in the YAML header,
comments and margin notes are not displayed at all, and highlightings and
`fixme` mark ups are suppressed (though the text is displayed). Also provided
are markup conventions for cross-references, index entries, and TikZ figures.

Copyright (C) 2017, 2018 Bennett Helm

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Syntax Extensions

## Block-Level Items:

Fenced DIV elements, with `comment`, `box`, `speaker`, and `center` are used
for creating special blocks. Most are self-explanatory, but `speaker` is used
for speaker notes in revealjs presentations. Fenced DIV elements take the
following form , where `comment`, `box`, `speaker` or `center` can fill in for
`CLASS`:

    ::: CLASS
    Text of block CLASS item...
    :::

FIXME: I cannot nest block elements nicely: boxed text within comment blocks
are not colored (but they are omitted when `draft` is false).

## Inline Items:

Note that tag-style inlines no longer work and should be switched to
span-style. Please change `<tag> ... </tag>` to `[...]{.tag}` in all documents.
In vim, the following regex works:

    %s/<\(!\?comment\|highlight\|fixme\|margin\|smcaps\)>\(.\{-}\)<\/\1>/[\2]{.\1}/gc

Here are the defined inlines:

    - `[...]{.comment}`:    make `...` be a comment
    - `[...]{.highlight}`:  make `...` be highlighted (note that this requires
                            that `soul.sty` be loaded in LaTeX)
    - `[...]{.fixme}`:      make `...` be a FixMe margin note (with
                            highlighting)
    - `[...]{.margin}`:     make `...` be a margin note
    - `[...]{.smcaps}`:     make `...` be in small caps


## Other Items:

Note that tag-style inlines no longer work and should be switched to
span-style. Please change `<tag> ... </tag>` to `[...]{.tag}` in all documents.
In vim, the following regex works (FIXME: UNTESTED!):

    %s/<\(l\|r\|rp\|i\)\s\+\([^>]\+\)>/[\2]{.\1}/gc

Here are the defined inlines:

    - `< `:                   (at begining of line) do not indent paragraph
                              (after quotation block or lists, e.g.)
    - `[LABEL]{.l}`:          create a label
    - `[LABEL]{.r}`:          create a reference
    - `[LABEL]{.rp}`:         create a page reference
    - `[text-for-index]{.i}`: create LaTeX index (`\\index{text-for-index}`)


## Images:

Allow for tikZ figures in code blocks. They should have the following format:

    ~~~ {#tikz caption='My *great* caption' id='fig:id' title='The title'
         tikzlibrary='items,to,go,in,\\usetikzlibrary{}'}

    [LaTeX code]

    ~~~

Note that the caption can be formatted text in markdown, but cannot use any
elements from this comment filter.

FIXME: Can I manually walk every item through this filter to fix this?

--]]

inspect = require('inspect')

-- Colors for various comment types
local COLORS = {}
COLORS.block_comment   = 'red'
COLORS.comment   = 'red'
COLORS.highlight = 'yellow'
COLORS.margin    = 'red'
COLORS.fixme     = 'cyan'

-- Location to save completed images
local HOME_PATH = os.getenv('HOME')
local IMAGE_PATH = HOME_PATH .. "/tmp/pandoc/Figures/"
-- Default font for `tikz` figures
local DEFAULT_FONT = 'fbb'


function html(text)
    return pandoc.RawInline("html", text)
end


function latex(text)
    return pandoc.RawInline("latex", text)
end


function docx(text)
    return pandoc.RawInline("openxml", text)
end


local LATEX_TEXT = {}
LATEX_TEXT.block_comment = {}
LATEX_TEXT.block_comment.Open = latex(string.format('\\color{%s}{}', COLORS.block_comment))
LATEX_TEXT.block_comment.Close = latex('\\color{black}{}')
LATEX_TEXT.block_box = {}
LATEX_TEXT.block_box.Open = latex('\\medskip\\begin{mdframed}')
LATEX_TEXT.block_box.Close = latex('\\end{mdframed}\\medskip{}')
LATEX_TEXT.block_center = {}
LATEX_TEXT.block_center.Open = latex('\\begin{center}')
LATEX_TEXT.block_center.Close = latex('\\end{center}')
LATEX_TEXT.block_speaker = {}  -- Note: treat <!speaker> just like <!comment>
LATEX_TEXT.block_speaker.Open = latex(string.format('\\textcolor{%s}{', COLORS.block_comment))
LATEX_TEXT.block_speaker.Close = latex('}')
LATEX_TEXT.comment = {}
LATEX_TEXT.comment.Open = latex(string.format('\\textcolor{%s}{', COLORS.comment))
LATEX_TEXT.comment.Close = latex('}')
LATEX_TEXT.highlight = {}
LATEX_TEXT.highlight.Open = latex('\\hl{')
LATEX_TEXT.highlight.Close = latex('}')
LATEX_TEXT.margin = {}
LATEX_TEXT.margin.Open = latex(string.format('\\marginpar{\\begin{flushleft}\\scriptsize{\\textcolor{%s}{', COLORS.margin))
LATEX_TEXT.margin.Close = latex('}}\\end{flushleft}}')
LATEX_TEXT.fixme = {}
LATEX_TEXT.fixme.Open = latex(string.format('\\marginpar{\\scriptsize{\\textcolor{%s}{Fix this!}}}\\textcolor{%s}{', COLORS.fixme, COLORS.fixme))
LATEX_TEXT.fixme.Close = latex('}')
LATEX_TEXT.noindent = latex('\\noindent{}')
LATEX_TEXT.l = {}
LATEX_TEXT.l.Open = '\\label{'
LATEX_TEXT.l.Close = '}'
LATEX_TEXT.r = {}
LATEX_TEXT.r.Open = '\\cref{'
LATEX_TEXT.r.Close = '}'
LATEX_TEXT.rp = {}
LATEX_TEXT.rp.Open = '\\cpageref{'
LATEX_TEXT.rp.Close = '}'

local HTML_TEXT = {}
HTML_TEXT.block_comment = {}
HTML_TEXT.block_comment.Open = html(string.format('<div style="color: %s;">', COLORS.block_comment))
HTML_TEXT.block_comment.Close = html('</div>')
HTML_TEXT.block_box = {}
HTML_TEXT.block_box.Open = html('<div style="border:1px solid black; padding:1.5ex;">')
HTML_TEXT.block_box.Close = html('</div>')
HTML_TEXT.block_center = {}
HTML_TEXT.block_center.Open = html('<div style="text-align:center";>')
HTML_TEXT.block_center.Close = html('</div>')
HTML_TEXT.block_speaker = {}  -- Note: treat <!speaker> just like <!comment>
HTML_TEXT.block_speaker.Open = html(string.format('<div style="color: %s;">', COLORS.block_comment))
HTML_TEXT.block_speaker.Close = html('</div>')
HTML_TEXT.comment = {}
HTML_TEXT.comment.Open = html(string.format('<span style="color: %s;">', COLORS.comment))
HTML_TEXT.comment.Close = html('</span>')
HTML_TEXT.highlight = {}
HTML_TEXT.highlight.Open = html('<mark>')
HTML_TEXT.highlight.Close = html('</mark>')
HTML_TEXT.margin = {}
HTML_TEXT.margin.Open = html(string.format('<span style="color: %s; %s">', COLORS.margin, MARGIN_STYLE))
HTML_TEXT.margin.Close = html('</span>')
HTML_TEXT.fixme = {}
HTML_TEXT.fixme.Open = html(string.format('<span style="color: %s; %s">Fix this!</span><span style="color: %s;">', COLORS.fixme, MARGIN_STYLE, COLORS.fixme))
HTML_TEXT.fixme.Close = html('</span>')
HTML_TEXT.noindent = html('<p class="noindent">')
HTML_TEXT.l = {}
HTML_TEXT.l.Open = '<a name="'
HTML_TEXT.l.Close = '"></a>'
HTML_TEXT.r = {}
HTML_TEXT.r.Open = '<a href="#'
HTML_TEXT.r.Close = '">here</a>'
HTML_TEXT.rp = {}
HTML_TEXT.rp.Open = '<a href="#'
HTML_TEXT.rp.Close = '">here</a>'

local REVEALJS_TEXT = {}
REVEALJS_TEXT.block_comment = {}
REVEALJS_TEXT.block_comment.Open = html(string.format('<div style="color: %s;">', COLORS.block_comment))
REVEALJS_TEXT.block_comment.Close = html('</div>')
REVEALJS_TEXT.block_box = {}
REVEALJS_TEXT.block_box.Open = html('<div style="border:1px solid black; padding:1.5ex;">')
REVEALJS_TEXT.block_box.Close = html('</div>')
REVEALJS_TEXT.block_center = {}
REVEALJS_TEXT.block_center.Open = html('<div style="text-align:center";>')
REVEALJS_TEXT.block_center.Close = html('</div>')
REVEALJS_TEXT.block_speaker = {}
REVEALJS_TEXT.block_speaker.Open = html('<aside class="notes">')
REVEALJS_TEXT.block_speaker.Close = html('</aside>')
REVEALJS_TEXT.comment = {}
REVEALJS_TEXT.comment.Open = html(string.format('<span style="color: %s;">', COLORS.comment))
REVEALJS_TEXT.comment.Close = html('</span>')
REVEALJS_TEXT.highlight = {}
REVEALJS_TEXT.highlight.Open = html('<mark>')
REVEALJS_TEXT.highlight.Close = html('</mark>')
REVEALJS_TEXT.margin = {}
REVEALJS_TEXT.margin.Open = html(string.format('<span style="color: %s; %s;">', COLORS.margin, MARGIN_STYLE))
REVEALJS_TEXT.margin.Close = html('</span>')
REVEALJS_TEXT.fixme = {}
REVEALJS_TEXT.fixme.Open = html(string.format('<span style="color: %s; %s">Fix this!</span><span style="color: %s;">', COLORS.fixme, MARGIN_STYLE, COLORS.fixme))
REVEALJS_TEXT.fixme.Close = html('</span>')
REVEALJS_TEXT.noindent = html('<p class="noindent">')
REVEALJS_TEXT.l = {}
REVEALJS_TEXT.l.Open = '<a name="'
REVEALJS_TEXT.l.Close = '"></a>'
REVEALJS_TEXT.r = {}
REVEALJS_TEXT.r.Open = '<a href="#'
REVEALJS_TEXT.r.Close = '">here</a>'
REVEALJS_TEXT.rp = {}
REVEALJS_TEXT.rp.Open = '<a href="#'
REVEALJS_TEXT.rp.Close = '">here</a>'

local DOCX_TEXT = {}
DOCX_TEXT.block_comment = {}
DOCX_TEXT.block_comment.Open = docx('')
DOCX_TEXT.block_comment.Close = docx('')
DOCX_TEXT.block_box = {}
DOCX_TEXT.block_box.Open = docx('')
DOCX_TEXT.block_box.Close = docx('')
DOCX_TEXT.block_center = {}
DOCX_TEXT.block_center.Open = docx('')
DOCX_TEXT.block_center.Close = docx('')
DOCX_TEXT.block_speaker = {}
DOCX_TEXT.block_speaker.Open = docx('')
DOCX_TEXT.block_speaker.Close = docx('')
DOCX_TEXT.comment = {}
DOCX_TEXT.comment.Open = docx('<w:rPr><w:color w:val="FF0000"/></w:rPr><w:t>')
DOCX_TEXT.comment.Close = docx('</w:t>')
DOCX_TEXT.highlight = {}
DOCX_TEXT.highlight.Open = docx('<w:rPr><w:highlight w:val="yellow"/></w:rPr><w:t>')
DOCX_TEXT.highlight.Close = docx('</w:t>')
DOCX_TEXT.margin = {}
DOCX_TEXT.margin.Open = docx('')
DOCX_TEXT.margin.Close = docx('')
DOCX_TEXT.fixme = {}
DOCX_TEXT.fixme.Open = docx('<w:rPr><w:color w:val="0000FF"/></w:rPr><w:t>')
DOCX_TEXT.fixme.Close = docx('</w:t>')
DOCX_TEXT.noindent = docx('')
DOCX_TEXT.l = {}
DOCX_TEXT.l.Open = ''
DOCX_TEXT.l.Close = ''
DOCX_TEXT.r = {}
DOCX_TEXT.r.Open = ''
DOCX_TEXT.r.Close = ''
DOCX_TEXT.rp = {}
DOCX_TEXT.rp.Open = ''
DOCX_TEXT.rp.Close = ''


-- Used to store YAML variables (to check for `draft` status and for potential
-- modification later).
local YAML_VARS = {}

-- Indicates whether any box element has been used. If so, need to load LaTeX
-- package.
local BOX_USED = false

-- html code for producing a margin comment
local MARGIN_STYLE = "max-width:20%; border: 1px solid black; padding: 1ex; margin: 1ex; float:right; font-size: small;"

-- Used to count words in text, abstract, and footnotes
local WORD_COUNT = 0
local ABSTRACT_COUNT = 0
local NOTE_COUNT = 0


function isHTML(text)
    if text == "html" or text == "html4" or text == "html5"  then
        return true
    else
        return false
    end
end


function isLaTeX(text)
    if text == "latex" or text == "beamer" then
        return true
    else
        return false
    end
end


function getYAML(meta)
    for key, value in pairs(meta) do
        if type(value) == "boolean" then
            YAML_VARS[key] = value
        elseif type(value) == "table" then
            YAML_VARS[key] = value
        end
    end
    if YAML_VARS.abstract then
        local abstract = YAML_VARS.abstract
        local content = ""
        if abstract.t == "MetaBlocks" then
            for _, block in pairs(abstract) do
                pandoc.walk_block(block, {
                    Str = function(string)
                        if string.text:match("%P") then
                            ABSTRACT_COUNT = ABSTRACT_COUNT + 1
                        end
                        return
                    end})
            end
        elseif abstract.t == "MetaInlines" then
            for _, inline in pairs(abstract) do
                if inline.t == "Str" and inline.text:match("%P") then
                    ABSTRACT_COUNT = ABSTRACT_COUNT + 1
                end
            end
        end
    end
    -- print("ABSTRACT: " .. ABSTRACT_COUNT)
end


function OLDgetYAML(meta)
    for key, value in pairs(meta) do
        if type(value) == "boolean" then
            YAML_VARS[key] = value
        elseif type(value) == "table" then
            YAML_VARS[key] = value
        end
    end
    if YAML_VARS["abstract"] then
        content = pandoc.utils.stringify(YAML_VARS["abstract"])
        _, words = content:gsub("%S+", "")
        ABSTRACT_COUNT = ABSTRACT_COUNT + words
    end
end


function setYAML(meta)
    if FORMAT == "markdown" then  -- Don't change anything if translating to .md
        return
    elseif BOX_USED and (isLaTeX(FORMAT)) then
        -- Need to add package for LaTeX
        local rawInlines = {pandoc.MetaInlines({latex("\\RequirePackage{mdframed}")})}
        if meta["header-includes"] == nil then
            meta["header-includes"] = pandoc.MetaList(rawInlines)
        else
            table.insert(meta["header-includes"], pandoc.MetaList(rawInlines))
        end
    end
    print(string.format("Words:%6d │ Abstract:%4d │ Notes:%5d │ Body:%6d", WORD_COUNT, ABSTRACT_COUNT, NOTE_COUNT, WORD_COUNT - NOTE_COUNT - ABSTRACT_COUNT))
    -- print("┌───────────────WORD COUNT──────────────┐")
    -- print(string.format("│ Body text:  %6d │ Notes:    %6d │", WORD_COUNT - NOTE_COUNT - ABSTRACT_COUNT, NOTE_COUNT))
    -- print(string.format("│ Total:      %6d │ Abstract: %6d │", WORD_COUNT,  ABSTRACT_COUNT))
    -- print("└────────────────────┴──────────────────┘")
    return meta
end

function isCommentBlock(text)
    return text == 'comment' or text == 'box' or text == 'center' or text == 'speaker'
end


function handleBlocks(block)
    if FORMAT == "markdown" then  -- Don't change anything if translating to .md
        return
    elseif isCommentBlock(block.classes[1]) then
        if not YAML_VARS.draft and (block.classes[1] == "comment" or block.classes[1] == "speaker") then
            return {}
        elseif isLaTeX(FORMAT) then
            if block.classes[1] == "box" then
                BOX_USED = true
            end
            prefix = pandoc.Plain({LATEX_TEXT["block_" .. block.classes[1]].Open})
            postfix = pandoc.Plain({LATEX_TEXT["block_" .. block.classes[1]].Close})
            return {prefix} .. block.content .. {postfix}
        elseif isHTML(FORMAT) then
            prefix = pandoc.Plain({HTML_TEXT["block_" .. block.classes[1]].Open})
            postfix = pandoc.Plain({HTML_TEXT["block_" .. block.classes[1]].Close})
            return {prefix} .. block.content .. {postfix}
        elseif FORMAT == "revealjs" then
            prefix = pandoc.Plain({HTML_TEXT["block_" .. block.classes[1]].Open})
            postfix = pandoc.Plain({HTML_TEXT["block_" .. block.classes[1]].Close})
            return {prefix} .. block.content .. {postfix}
        elseif FORMAT == "docx" then
            prefix = pandoc.Plain({DOCX_TEXT["block_" .. block.classes[1]].Open})
            postfix = pandoc.Plain({DOCX_TEXT["block_" .. block.classes[1]].Close})
            return {prefix} .. block.content .. {postfix}
        end
    end
end


function handlePars(para)
    if FORMAT == "markdown" then  -- Don't change anything if translating to .md
        return
    elseif #para.content > 2 and para.content[1].text == "<" and para.content[2].t == 'Space' then
        -- Don't indent paragraph that starts with "< "
        if isLaTeX(FORMAT) then
            return pandoc.Para({LATEX_TEXT.noindent, table.unpack(para.content, 3, #para.content)})
        elseif isHTML(FORMAT) then
            return pandoc.Plain({HTML_TEXT.noindent, table.unpack(para.content, 3, #para.content)})
        elseif FORMAT == "revealjs" then
            return pandoc.Plain({REVEALJS_TEXT.noindent, table.unpack(para.content, 3, #para.content)})
        elseif FORMAT == "docx" then
            return pandoc.Plain({DOCX_TEXT.noindent, table.unpack(para.content, 3, #para.content)})
        end
    end
end

local CURRENT_COLOR = "black"

function handleInlines(span)
    if FORMAT == "markdown" then  -- Don't change anything if translating to .md
        return
    elseif span.classes[1] == "comment" or span.classes[1] == "margin" or span.classes[1] == "fixme" or span.classes[1] == "highlight" then
        if not YAML_VARS.draft then
            if span.classes[1] == "fixme" or span.classes[1] == "highlight" then
                return span.content
            else
                return {}
            end
        elseif isLaTeX(FORMAT) then
            local prefix = {LATEX_TEXT[span.classes[1]].Open}
            local postfix = {LATEX_TEXT[span.classes[1]].Close}
            return prefix .. span.content .. postfix
        elseif isHTML(FORMAT) then
            local prefix = {HTML_TEXT[span.classes[1]].Open}
            local postfix = {HTML_TEXT[span.classes[1]].Close}
            return prefix .. span.content .. postfix
        elseif FORMAT == "revealjs" then
            local prefix = {REVEALJS_TEXT[span.classes[1]].Open}
            local postfix = {REVEALJS_TEXT[span.classes[1]].Close}
            return prefix .. span.content .. postfix
        elseif FORMAT == "docx" then
            local prefix = {DOCX_TEXT[span.classes[1]].Open}
            local postfix = {DOCX_TEXT[span.classes[1]].Close}
            return prefix .. span.content .. postfix
        end
    elseif span.classes[1] == "smcaps" then
        return pandoc.SmallCaps(span.content)
    elseif span.classes[1] == "i" then
        if isLaTeX(FORMAT) then
            return {latex("\\index{" .. pandoc.utils.stringify(span) .. "}")}
        else
            return {}
        end
    -- TODO: Everything below needs testing! (Should I be returning tables?)
    elseif span.classes[1] == "l" or span.classes[1] == "r" or span.classes[1] == "rp" then
        content = pandoc.utils.stringify(span.content)
        if isLaTeX(FORMAT) then
            local prefix = LATEX_TEXT[span.classes[1]].Open
            local postfix = LATEX_TEXT[span.classes[1]].Close
            return {latex(prefix .. content .. postfix)}
        elseif isHTML(FORMAT) then
            local prefix = HTML_TEXT[span.classes[1]].Open
            local postfix = HTML_TEXT[span.classes[1]].Close
            return {html(prefix .. content .. postfix)}
        elseif FORMAT == "revealjs" then
            local prefix = REVEALJS_TEXT[span.classes[1]].Open
            local postfix = REVEALJS_TEXT[span.classes[1]].Close
            return {html(prefix .. content .. postfix)}
        elseif FORMAT == "docx" then
            local prefix = DOCX_TEXT[span.classes[1]].Open
            local postfix = DOCX_TEXT[span.classes[1]].Close
            return {docx(prefix .. content .. postfix)}
        end
    end
end


function tikz2image(tikz, filetype, outfile)
    local tmphead = os.tmpname()
    local tmpdir = string.match(tmphead, "^(.*[\\/])") or "."
    local f = io.open(tmphead .. ".tex", 'w')
    f:write(tikz)
    f:close()
    os.execute("pdflatex -output-directory " .. tmpdir .. " " .. tmphead)
    if filetype == '.pdf' then
        os.rename(tmphead .. ".pdf", outfile)
    else
        os.execute("convert -density 300 " .. tmphead .. ".pdf -quality 100 " .. outfile)
    end
    os.remove(tmphead .. ".tex")
    os.remove(tmphead .. ".pdf")
    os.remove(tmphead .. ".log")
    os.remove(tmphead .. ".aux")
end


function handleCode(code)
    if code.classes[1] == 'tikz' then
        local font = DEFAULT_FONT
        if YAML_VARS.fontfamily then
            font = YAML_VARS.fontfamily[1].c
        end
        local filetype = "png"
        if isLaTeX(FORMAT) then
            filetype = ".pdf"
        end
        local outfile = IMAGE_PATH .. pandoc.sha1(code.text .. font) .. "." .. filetype
        local caption = code.attributes.caption or ""
        local formattedCaption = pandoc.read(caption).blocks[1].c
        local library = code.attributes.tikzlibrary or ""
        local codeHeader = "\\documentclass{standalone}\n" ..
                           "\\usepackage{" .. font .. "}\n" ..
                           "\\usepackage{tikz}\n"
        if library then
            codeHeader = codeHeader .. "\\usetikzlibrary{" .. library .. "}\n"
        end
        codeHeader = codeHeader .. "\\begin{document}\n"
        local codeFooter = "\n\\end{document}\n"
        tikz2image(codeHeader .. code.text .. codeFooter, filetype, outfile)
        print('Created image ' .. outfile)
        local title = code.attributes.title or ""
        local attr = pandoc.Attr(code.identifier, code.classes, code.attributes)
        return pandoc.Para({pandoc.Image(formattedCaption, outfile, title, attr)})
    end
end


function handleStrings(string)
    if string.text:match("%P") then
        WORD_COUNT = WORD_COUNT + 1
    end
    return
end


function handleNotes(note)
    return pandoc.walk_inline(note, {
        Str = function(string)
            if string.text:match("%P") then
                NOTE_COUNT = NOTE_COUNT + 1
            end
            return
        end})
end


return {
    {Meta = getYAML},
    {Span = handleInlines},
    {Para = handlePars},
    {Div = handleBlocks},
    {CodeBlock = handleCode},
    {Note = handleNotes},
    {Str = handleStrings},
    {Meta = setYAML}
}
