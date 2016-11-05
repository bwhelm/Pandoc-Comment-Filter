#!/usr/bin/env python

"""
Pandoc filter to extend the use of RawInline and RawBlocks to highlight
or comment on text. In draft mode, both are displayed in red; in
non-draft mode, only highlights are displayed, and that only in black.

Copyright (C) 2016 Bennett Helm

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

`<!comment>`:  begin comment block
`</!comment>`: end comment block
`<center>`:    begin centering
`</center>`:   end centering
`<!box>`:      begin frame box
`</!box>`:     end frame box
`<!speaker>`:  begin speaker notes (for revealjs)
`</!speaker>`: end speaker notes


## Inline Items:

`<comment>`:    begin commenting
`</comment>`:   end commenting
`<highlight>`:  begin highlighting (note that this requires that `soul.sty`
                    be loaded in LaTeX)
`</highlight>`: end highlighting
`<fixme>`:      begin FixMe margin note (and highlighting)
`</fixme>`:     end FixMe margin note (and highlighting)
`<margin>`:     begin margin note
`</margin>`:    end margin note


## Other Items:

`< `:                 do not indent paragraph (after quotation block or
                          lists, e.g.)
`<l LABEL>`:          create a label
`<r LABEL>`:          create a reference
`<rp LABEL>`:         create a page reference
`<i text-for-index>`: create a LaTeX index mark (`\\index{text-for-index}`)


## Images: Allow for tikZ figures in code blocks. They should have the
   following format:

~~~ {#tikz caption='My *great* caption' id='fig:id'
     tikzlibrary='items,to,go,in,\\usetikzlibrary{}'}

[LaTeX code]

~~~

Note that the caption can be formatted text in markdown.

"""

from os import path, mkdir, chdir, getcwd
from sys import getfilesystemencoding, stderr, stdout
from shutil import copyfile, rmtree
from subprocess import call, Popen, PIPE
from hashlib import sha1
from pandocfilters import toJSONFilter, RawInline, Para, Plain, Image, Str

IMAGE_PATH = path.expanduser('~/tmp/pandoc/Figures')
DEFAULT_FONT = 'fbb'
INLINE_TAG_STACK = []
BLOCK_COMMENT = False
INLINE_COMMENT = False
INLINE_MARGIN = False
INLINE_HIGHLIGHT = False
INLINE_FONT_COLOR_STACK = ['black']

COLORS = {
    '<!comment>': 'red',
    '<comment>': 'red',
    '<highlight>': 'yellow',
    '<margin>': 'red',
    '<fixme>': 'cyan'
}

# HTML style for margin notes
MARGIN_STYLE = 'max-width:20%; border: 1px solid black; padding: 1ex; margin: 1ex; float:right; font-size: small;'

LATEX_TEXT = {
    '<!comment>': '\\color{{{}}}{{}}'.format(COLORS['<!comment>']),
    '</!comment>': '\\color{black}{}',
    '<!box>': '\\medskip\\noindent\\fbox{\\begin{minipage}[t]{0.98\\columnwidth}',
    '</!box>': '\\end{minipage}}\\medskip{}',
    '<comment>': '\\color{{{}}}{{}}'.format(COLORS['<comment>']),
    '</comment>': '',
    '<highlight>': '\\hl{',
    '</highlight>': '}',
    '<margin>': '\\marginpar{{\\footnotesize{{\\color{{{}}}{{}}'.format(COLORS['<margin>']),
    '</margin>': '}}',
    '<fixme>': '\\marginpar{{\\footnotesize{{\\color{{{}}}{{}}Fix this!}}}}\\color{{{}}}{{}}'.format(COLORS['<fixme>'], COLORS['<fixme>']),
    '</fixme>': '',
    '<center>': '\\begin{center}',  # TODO Need to figure out what to do for beamer!
    '</center>': '\\end{center}',
    '<!speaker>': '\\color{{{}}}{{}}'.format(COLORS['<!comment>']),  # Note: treat this just like <!comment>
    '</!speaker>': '\\color{black}{}'
}
HTML_TEXT = {
    '<!comment>': '<div style="color: {};">'.format(COLORS['<!comment>']),
    '</!comment>': '</div>',
    '<comment>': '<span style="color: {};">'.format(COLORS['<comment>']),
    '</comment>': '</span>',
    '<highlight>': '<mark>',
    '</highlight>': '</mark>',
    '<margin>': '<span style="color: {}; {}">'.format(COLORS['<margin>'], MARGIN_STYLE),
    '</margin>': '</span>',
    '<fixme>': '<span style="color: {}; {}">Fix this!</span><span style="color: {};">'.format(COLORS['<fixme>'], MARGIN_STYLE, COLORS['<fixme>']),
    '</fixme>': '</span>',
    '<center>': '<div style="text-align:center";>',
    '</center>': '</div>',
    '<!box>': '<div style="border:1px solid black; padding:1.5ex;">',
    '</!box>': '</div>',
    '<!speaker>': '<div style="color: {};">'.format(COLORS['<!comment>']),  # Note: treat this just like <!comment>
    '</!speaker>': '</div>'
}
REVEALJS_TEXT = {
    '<!comment>': '<div style="color: {};">'.format(COLORS['<!comment>']),
    '</!comment>': '</div>',
    '<comment>': '<span style="color: {};">'.format(COLORS['<comment>']),
    '</comment>': '</span>',
    '<highlight>': '<mark>',
    '</highlight>': '</mark>',
    '<margin>': '<span style="color: {}; {};">'.format(COLORS['<margin>'], MARGIN_STYLE),
    '</margin>': '</span>',
    '<fixme>': '<span style="color: {}; {}">Fix this!</span><span style="color: {};">'.format(COLORS['<fixme>'], MARGIN_STYLE, COLORS['<fixme>']),
    '</fixme>': '</span>',
    '<center>': '<div style="text-align:center";>',
    '</center>': '</div>',
    '<!box>': '<div style="border:1px solid black; padding:1.5ex;">',
    '</!box>': '</div>',
    '<!speaker>': '<aside class="notes">',
    '</!speaker>': '</aside>'
}


def debug(text):
    stderr.write(text)


def my_sha1(x):
    return sha1(x.encode(getfilesystemencoding())).hexdigest()


def tikz2image(tikz, filetype, outfile):
    from tempfile import mkdtemp
    tmpdir = mkdtemp()
    olddir = getcwd()
    chdir(tmpdir)
    f = open('tikz.tex', 'w')
    f.write(tikz)
    f.close()
    p = call(['pdflatex', 'tikz.tex'], stdout=stdout)
    chdir(olddir)
    if filetype == '.pdf':
        copyfile(path.join(tmpdir, 'tikz.pdf'), outfile + filetype)
    else:
        call(['convert', '-density', '300', path.join(tmpdir, 'tikz.pdf'), '-quality', '100', outfile + filetype])
    rmtree(tmpdir)


def toFormat(string, fromThis, toThis):
    # Process string through pandoc to get formatted JSON string.
    p1 = Popen(['echo'] + string.split(), stdout=PIPE)
    p2 = Popen(['pandoc', '-f', fromThis, '-t', toThis], stdin=p1.stdout,
               stdout=PIPE)
    p1.stdout.close()
    return p2.communicate()[0].decode('utf-8').strip('\n')


def latex(text):
    return RawInline('latex', text)


def html(text):
    return RawInline('html', text)


def handle_comments(key, value, docFormat, meta):
    global INLINE_TAG_STACK, BLOCK_COMMENT, INLINE_COMMENT, INLINE_MARGIN,\
        INLINE_HIGHLIGHT, INLINE_FONT_COLOR_STACK

    # If translating to markdown, leave everything alone.
    if docFormat == 'markdown':
        return

    # Get draft status from metadata field (or assume not draft if there's
    # no such field)
    try:
        draft = meta['draft']['c']
    except KeyError:
        draft = False

    # Check to see if we're starting or closing a Block element
    if key == 'RawBlock':
        elementFormat, tag = value
        if elementFormat != 'html':
            return
        tag = tag.lower()

        if not draft:
            if BLOCK_COMMENT:  # Need to suppress output
                if tag == '</!comment>':
                    BLOCK_COMMENT = False
                return []

        # Not currently suppressing output ...

        if tag in ['<!comment>', '<!box>', '<center>', '<!speaker>']:
            if tag == '<!comment>':
                BLOCK_COMMENT = True
                if not draft:
                    return []
                INLINE_FONT_COLOR_STACK.append(COLORS[tag])
            if docFormat == 'latex':
                return Para([latex(LATEX_TEXT[tag])])
                # FIXME: What about beamer?
            elif docFormat in ['html', 'html5']:
                return Plain([html(HTML_TEXT[tag])])
            elif docFormat == 'revealjs':
                return Plain([html(REVEALJS_TEXT[tag])])
            else:
                return
        elif tag in ['</!comment>', '</!box>', '</center>', '</!speaker>']:
            if INLINE_TAG_STACK:
                debug('Need to close all inline elements before closing block elements!\n\n{}\n\nbefore\n\n{}\n\n'.format(str(INLINE_TAG_STACK), tag))
                exit(1)
            if tag == '</!comment>':
                BLOCK_COMMENT = False
                if not draft:
                    return []
                INLINE_FONT_COLOR_STACK.pop()
            if docFormat == 'latex':
                return Para([latex(LATEX_TEXT[tag])])
                # FIXME: What about beamer?
            elif docFormat in ['html', 'html5']:
                return Plain([html(HTML_TEXT[tag])])
            elif docFormat == 'revealjs':
                return Plain([html(REVEALJS_TEXT[tag])])
            else:
                return
        else:
            return  # TODO Is this the right thing to do?

    if not draft and BLOCK_COMMENT:
        return []  # Need to suppress output

    # Then check to see if we're changing INLINE_TAG_STACK...
    elif key == 'RawInline':
        elementFormat, tag = value
        if elementFormat != 'html':
            return

        # Check to see if need to suppress output. We do this only for
        # `<comment>` and `<margin>` tags; with `<fixme>` and `<highlight>`
        # tags, we merely suppress the tag.
        if not draft:
            if tag == '<comment>':
                INLINE_COMMENT = True
                return []
            elif tag == '<margin>':
                INLINE_MARGIN = True
                return []
            elif INLINE_COMMENT:  # Need to suppress output
                if tag == '</comment>':
                    INLINE_COMMENT = False
                return []
            elif INLINE_MARGIN:  # Need to suppress output
                if tag == '</margin>':
                    INLINE_MARGIN = False
                return []
            elif tag in ['<fixme>', '<highlight>', '</fixme>',
                         '</highlight>']:
                return []  # Suppress the tag (but not the subsequent text)

        # Not currently suppressing output....

        if tag in ['<comment>', '<fixme>', '<margin>', '<highlight>',
                   '</comment>', '</fixme>', '</margin>', '</highlight>']:
            # LaTeX gets treated differently than HTML
            if docFormat in ['latex', 'beamer']:
                preText = ''
                postText = ''
                # Cannot change COLORS within highlighting in LaTeX (but
                # don't do anything when closing the highlight tag!)
                if INLINE_HIGHLIGHT and tag != '</highlight>':
                    preText = LATEX_TEXT['</highlight>']
                    postText = LATEX_TEXT['<highlight>']
                if tag in ['<comment>', '<fixme>', '<margin>',
                           '<highlight>']:  # If any opening tag
                    if tag == '<comment>':
                        INLINE_COMMENT = True
                        INLINE_FONT_COLOR_STACK.append(COLORS[tag])
                    elif tag == '<fixme>':
                        INLINE_FONT_COLOR_STACK.append(COLORS[tag])
                    elif tag == '<margin>':
                        INLINE_MARGIN = True
                        INLINE_FONT_COLOR_STACK.append(COLORS[tag])
                    elif tag == '<highlight>':
                        INLINE_HIGHLIGHT = True
                        INLINE_FONT_COLOR_STACK.append(
                            INLINE_FONT_COLOR_STACK[-1])
                    INLINE_TAG_STACK.append(tag)
                    return latex(preText + LATEX_TEXT[tag] + postText)
                elif tag in ['</comment>', '</fixme>', '</margin>',
                             '</highlight>']:
                    if tag == '</comment>':
                        INLINE_COMMENT = False
                    elif tag == '</fixme>':
                        pass
                    elif tag == '</margin>':
                        INLINE_MARGIN = False
                    elif tag == '</highlight>':
                        INLINE_HIGHLIGHT = False
                    INLINE_FONT_COLOR_STACK.pop()
                    previousColor = INLINE_FONT_COLOR_STACK[-1]
                    currentInlineStatus = INLINE_TAG_STACK.pop()
                    if currentInlineStatus[1:] == tag[2:]:
                        # matching opening tag
                        return latex('{}{}\\color{{{}}}{{}}{}'.format(preText,
                                     LATEX_TEXT[tag], previousColor,
                                     postText))
                    else:
                        debug('Closing tag ({}) does not match opening tag ({}).\n\n'.format(tag, currentInlineStatus))
                        exit(1)
            else:  # Some docFormat other than LaTeX/beamer
                if tag in ['<comment>', '<fixme>', '<margin>',
                           '<highlight>']:
                    if tag == '<highlight>':
                        INLINE_HIGHLIGHT = True
                    INLINE_TAG_STACK.append(tag)
                else:
                    if tag == '</highlight>':
                        INLINE_HIGHLIGHT = False
                    INLINE_TAG_STACK.pop()
                if docFormat in ['html', 'html5']:
                    return html(HTML_TEXT[tag])
                elif docFormat == 'revealjs':
                    return html(REVEALJS_TEXT[tag])
                else:
                    return []

        elif tag.startswith('<i ') and tag.endswith('>'):  # Index
            if docFormat == 'latex':
                return latex('\\index{{{}}}'.format(tag[3:-1]))
            else:
                return []

        elif tag.startswith('<l ') and tag.endswith('>'):
            # My definition of a label
            if docFormat == 'latex':
                return latex('\\label{{{}}}'.format(tag[3:-1]))
            elif docFormat in ['html', 'html5']:
                return html('<a name="{}"></a>'.format(tag[3:-1]))

        elif tag.startswith('<r ') and tag.endswith('>'):
            # My definition of a reference
            if docFormat == 'latex':
                return latex('\\cref{{{}}}'.format(tag[3:-1]))
            elif docFormat in ['html', 'html5']:
                return html('<a href="#{}">here</a>'.format(tag[3:-1]))

        elif tag.startswith('<rp ') and tag.endswith('>'):
            # My definition of a page reference
            if docFormat == 'latex':
                return latex('\\cpageref{{{}}}'.format(tag[4:-1]))
            elif docFormat in ['html', 'html5']:
                return html('<a href="#{}">here</a>'.format(tag[4:-1]))

    elif not draft and (INLINE_COMMENT or INLINE_MARGIN):
        # Suppress all output
        return []

    # Check some cases at beginnings of paragraphs
    elif key == 'Para':
        try:
            # If translating to LaTeX, beginning a paragraph with '< '
            # will cause '\noindent{}' to be output first.
            if value[0]['t'] == 'Str' and value[0]['c'] == '<' \
                    and value[1]['t'] == 'Space':
                if docFormat == 'latex':
                    return Para([latex('\\noindent{}')] + value[2:])
                elif docFormat in ['html', 'html5']:
                    return Para([html('<div class="noindent">')] +
                                value[2:] + [html('</div>')])
                else:
                    return Para(value[2:])

            else:
                return  # Normal paragraph, not affected by this filter

        except:
            return  # May happen if the paragraph is empty.

    # Check for tikz CodeBlock. If it exists, try typesetting figure
    elif key == 'CodeBlock':
        (id, classes, attributes), code = value
        if 'tikz' in classes or '\\begin{tikzpicture}' in code:
            if 'fontfamily' in meta:
                font = meta['fontfamily']['c'][0]['c']
            else:
                font = DEFAULT_FONT
            outfile = path.join(IMAGE_PATH, my_sha1(code + font))
            filetype = '.pdf' if docFormat == 'latex' else '.png'
            sourceFile = outfile + filetype
            caption = ''
            library = ''
            for a, b in attributes:
                if a == 'caption':
                    caption = b
                elif a == 'tikzlibrary':
                    library = b
            if not path.isfile(sourceFile):
                try:
                    mkdir(IMAGE_PATH)
                    debug('Created directory {}\n\n'.format(IMAGE_PATH))
                except OSError:
                    pass
                codeHeader = '\\documentclass{{standalone}}\n\\usepackage{{{}}}\n\\usepackage{{tikz}}\n'.format(font)
                if library:
                    codeHeader += '\\usetikzlibrary{{{}}}\n'.format(library)
                codeHeader += '\\begin{document}\n'
                codeFooter = '\n\\end{document}\n'
                tikz2image(codeHeader + code + codeFooter, filetype,
                           outfile)
                debug('Created image {}\n\n'.format(sourceFile))
            if caption:
                # Need to run this through pandoc to get JSON
                # representation so that captions can be docFormatted text.
                jsonString = toFormat(caption, 'markdown', 'json')
                if "blocks" in jsonString:
                    formattedCaption = eval(jsonString)["blocks"][0]['c']
                else:  # old API
                    formattedCaption = eval(jsonString)[1][0]['c']
            else:
                formattedCaption = [Str('')]
            return Para([Image((id, classes, attributes), formattedCaption, [sourceFile, caption])])
        else:  # CodeBlock, but not tikZ
            return

    else:  # Not text this filter modifies....
        return


if __name__ == "__main__":
    toJSONFilter(handle_comments)
