#!/usr/bin/env python

'''
Pandoc filter to extend the use of RawInline and RawBlocks to highlight 
or comment on text. In draft mode, both are displayed in red; in 
non-draft mode, only highlights are displayed, and that only in black.

Copyright (C) 2015 Bennett Helm 

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

`<!comment>`:	begin comment block (or speaker notes for revealjs)
`</!comment>`:	end comment block (or speaker notes for revealjs)
`<center>`:		begin centering
`</center>`:	end centering
`<!box>`:		begin frame box
`</!box>`:		end frame box


## Inline Items:

`<comment>`:	begin commenting
`</comment>`:	end commenting
`<highlight>`:	begin highlighting (note that this requires that `soul.sty` 
				be loaded in LaTeX)
`</highlight>`:	end highlighting
`<fixme>`:		begin FixMe margin note (and highlighting)
`</fixme>`:		end FixMe margin note (and highlighting)
`<margin>`:		begin margin note
`</margin>`:	end margin note


## Other Items:

`< `:			do not indent paragraph (after quotation block or lists, e.g.)
`<l LABEL>`:	create a label
`<r LABEL>`:	create a reference
`<rp LABEL>`:	create a page reference
`<i text-for-index>`: create a LaTeX index mark (`\\index{text-for-index}`)


## Images: Allow for tikZ figures in code blocks. They should have the following
   format:

~~~ {#tikz caption='Caption' id='fig:id' tikzlibrary='items,to,go,in,\\usetikzlibrary{}'}

[LaTeX code]

~~~

'''

from pandocfilters import toJSONFilter, RawInline, Para, Plain, Image, Str
from os import path, mkdir, chdir, getcwd
from shutil import copyfile, rmtree
from sys import getfilesystemencoding, stderr # Use `print(something, file=stderr)` for debugging
from tempfile import mkdtemp
from subprocess import call
from hashlib import sha1

IMAGE_PATH = '/Users/bennett/tmp/pandoc/Figures'

BLOCK_STATUS = []
INLINE_STATUS = []
HIGHLIGHT_STATUS = False

colors = {
	'<!comment>': 'red', 
	'<comment>': 'red', 
	'<highlight>': 'yellow',
	'<margin>': 'red',
	'<fixme>': 'cyan',
}
endColor = '\\color{black}{}'
marginStyle = 'max-width:20%; border: 1px solid black; padding: 1ex; margin: 1ex; float:right; font-size: small;' # HTML style for margin notes

latexText = {
	'<!comment>': '\\color{' + colors['<!comment>'] + '}{}',
	'</!comment>': endColor,
	'<!box>': '\\medskip\\noindent\\fbox{\\begin{minipage}[t]{0.98\\columnwidth}',
	'</!box>': '\\end{minipage}}\medskip{}',
	'<comment>': '\\color{' + colors['<comment>'] + '}{}',
	'</comment>': endColor,
	'<highlight>': '\\hl{',
	'</highlight>': '}',
	'<margin>': '\\marginpar{\\footnotesize{\\color{' + colors['<margin>'] + '}{}',
	'</margin>': '}}',
	'<fixme>': '\\marginpar{\\footnotesize{\\color{' + colors['<fixme>'] + '}{}Fix this!}}\\color{' + colors['<fixme>'] + '}{}',
	'</fixme>': endColor,
	'<center>': '\\begin{center}', # TODO Need to figure out what to do for beamer!
	'</center>': '\\end{center}',
}
htmlText = {
	'<!comment>': '<div style="color: ' + colors['<!comment>'] + ';">',
	'</!comment>': '</div>',
	'<comment>': '<span style="color: ' + colors['<comment>'] + ';">',
	'</comment>': '</span>',
	'<highlight>': '<mark>',
	'</highlight>': '</mark>',
	'<margin>': '<span style="color: ' + colors['<margin>'] + '; ' + marginStyle + '">',
	'</margin>': '</span>',
	'<fixme>': '<span style="color: ' + colors['<fixme>'] + '; ' + marginStyle + '">Fix this!</span><span style="color: ' + colors['<fixme>'] + ';">',
	'</fixme>': '</span>',
	'<center>': '<div style="text-align:center";>',
	'</center>': '</div>',
	'<!box>': '<div style="border:1px solid black; padding:1.5ex;">',
	'</!box>': '</div>',
}
revealjsText = { # TODO Fill this out where needed!
	'<!comment>': '<aside class="notes">',
	'</!comment>': '</aside>',
	'<comment>': '<span style="color: ' + colors['<comment>'] + ';">',
	'</comment>': '</span>',
	'<highlight>': '<mark>',
	'</highlight>': '</mark>',
	'<margin>': '',
	'</margin>': '',
	'<fixme>': '',
	'</fixme>': '',
	'<center>': '',
	'</center>': '',
	'<!box>': '<div style="border:1px solid black; padding:1.5ex;">',
	'</!box>': '</div>',
}

def my_sha1(x):
	return sha1(x.encode(getfilesystemencoding())).hexdigest()

def tikz2image(tikz, filetype, outfile, library):
	tmpdir = mkdtemp()
	olddir = getcwd()
	chdir(tmpdir)
	f = open('tikz.tex', 'w')
	f.write('\\documentclass{standalone}\n\\usepackage{tikz}\n')
	if library: f.write('\\usetikzlibrary{' + library + '}\n')
	f.write('\\begin{document}\n')
	f.write(tikz)
	f.write('\n\\end{document}\n')
	f.close()
	p = call(['pdflatex', 'tikz.tex'], stdout=stderr)
	chdir(olddir)
	if filetype == 'pdf':
		copyfile(path.join(tmpdir, 'tikz.pdf'), outfile + '.' + filetype)
	else:
		call(['convert', path.join(tmpdir, 'tikz.pdf'), outfile + '.' + filetype])
	rmtree(tmpdir)

def latex(text):
	return RawInline('latex', text)

def html(text):
	return RawInline('html', text)
	
def closeHtmlSpan(oldInlineStatus):
	if oldInlineStatus in ['<comment>', '<highlight>', '<fixme>']: return '</span>'
	else: return ''

def closeHtmlDiv(oldBlockStatus):
	if oldBlockStatus in ['<!comment>']: return '</div>'
	else: return ''

def handle_comments(key, value, format, meta):
	global BLOCK_STATUS, INLINE_STATUS, HIGHLIGHT_STATUS
	
	# If translating to markdown, leave everything alone.
	if format == 'markdown': return
	
	# Get draft status from metadata field (or assume not draft if there's no such field)
	try: draft = meta['draft']['c']
	except KeyError: draft = False
	
	# Check to see if we're changing BLOCK_STATUS...
	if key == 'RawBlock':
		type, tag = value
		if type != 'html': pass
		tag = tag.lower()
		if tag in ['<!comment>', '<center>']:
			BLOCK_STATUS.append(tag)
			if not draft and format != 'revealjs' and tag not in ['<center>']: return []
			elif format == 'latex':
				if HIGHLIGHT_STATUS: return Para([latex(latexText['</highlight>'] + latexText[tag] + latexText['<highlight>'])])
				else: return Para([latex(latexText[tag])])
			elif format[:4] == 'html' or (format == 'revealjs' and tag == '<!highlight>'):
				return Plain([html(htmlText[tag])])
			elif format == 'revealjs':
				return Plain([html(revealjsText[tag])])
			else: return []
			
		elif tag in ['</!comment>', '</center>']:
			currentBlockStatus = BLOCK_STATUS.pop()
			if currentBlockStatus[1:] == tag[2:]: # If we have a matching closing tag...
				if not draft and tag not in ['</center>']: return []
				if format == 'latex':
					preText = ''
					if BLOCK_STATUS: tag = BLOCK_STATUS[-1] # Switch back to previous
					if HIGHLIGHT_STATUS: return Para([latex(latexText['</highlight>'] + latexText[tag] + latexText['<highlight>'])])
					else: return Para([latex(latexText[tag])])
				elif format[0:4] == 'html':
					return Plain([html(htmlText[tag])])
				elif format == 'revealjs':
					return Plain([html(revealjsText[tag])])
				else: return []
			else: exit(1) # TODO Is this the right thing to do?
		elif tag in ['<!box>', '</!box>'] and not(draft == False and '<!comment>' in BLOCK_STATUS):
			# Note that when the box is nested inside a `<!comment>` block and 
			# draft == False, I want no box at all. The above conditional does this.
			if format == 'latex': return Para([latex(latexText[tag])])
			elif format[:4] == 'html': return Plain([html(htmlText[tag])])
			elif format == 'revealjs': return Plain([html(revealjsText[tag])])
			else: return [] # TODO Is this the right thing to do?
			
	# Then check to see if we're changing INLINE_STATUS...
	elif key == 'RawInline':
		type, tag = value
		if type != 'html': pass
		tag = tag.lower()
		
		if tag == '<highlight>': # Highlight needs to be handled separately (and cannot have text color changed inside the highlighting).
			if HIGHLIGHT_STATUS == True: return
			HIGHLIGHT_STATUS = True
			if format in ['latex', 'beamer']:
				return latex(latexText[tag])
			elif format in ['html', 'html5', 'revealjs']:
				return html(htmlText[tag])
			else: return []
		elif tag == '</highlight>':
			if HIGHLIGHT_STATUS == False: return
			HIGHLIGHT_STATUS = False
			if format in ['latex', 'beamer']:
				newText = latexText[tag]
				return latex(newText)
			elif format in ['html', 'html5', 'revealjs']: return html(htmlText[tag])
		elif tag in ['<margin>', '<comment>', '<fixme>']:
			INLINE_STATUS.append(tag)
			if not draft: return []
			elif format in ['latex', 'beamer']:
				if HIGHLIGHT_STATUS: return latex(latexText['</highlight>'] + latexText[tag] + latexText['<highlight>'])
				else: return latex(latexText[tag])
			elif format in ['html', 'html5', 'revealjs']:
				return html(htmlText[tag])
			else: return []
		
		elif tag in ['</margin>', '</comment>', '</fixme>']:
			currentInlineStatus = INLINE_STATUS.pop()
			if currentInlineStatus[1:] == tag[2:]: # If we have a matching closing tag...
				if not draft: return []
				elif format in ['latex', 'beamer']:
					preText = ''
					postText = ''
					if HIGHLIGHT_STATUS: 
						preText = latexText['</highlight>']
						postText = latexText['<highlight>']
					if INLINE_STATUS: # Need to switch back to previous inline ...
						if INLINE_STATUS[-1] == '<margin>': newText = latexText['<comment>'] # TODO Need to find a more general solution that works for `<fixme>` as well.
						else: newText = latexText[INLINE_STATUS[-1]]
						if tag == '</margin>': newText = latexText[tag] + newText # Need to close the margin environment before switching back
					elif BLOCK_STATUS: 
						newText = latexText[BLOCK_STATUS[-1]] # ... or to previous block
						if tag == '</margin>': newText = latexText[tag] + newText # Need to close the margin environment before switching back
					else: newText = latexText[tag]
					return latex(preText + newText + postText)
				elif format in ['html', 'html5', 'revealjs']: return html(htmlText[tag])
			else: exit(1) # TODO Is this the right thing to do?
		
		elif tag.startswith('<i ') and tag.endswith('>'): # Index
			indexText = tag[3:-1]
			if format == 'latex': return latex('\\index{' + indexText + '}')
			else: return []
			
		elif tag.startswith('<l ') and tag.endswith('>'): # My definition of a label
			label = tag[3:-1]
			if format == 'latex': return latex('\\label{' + label + '}')
			elif format[0:4] == 'html': return html('<a name="' + label + '"></a>')
			
		elif tag.startswith('<r ') and tag.endswith('>'): # My definition of a reference
			label = tag[3:-1]
			if format == 'latex': return latex('\\cref{' + label + '}')
			elif format[0:4] == 'html': return html('<a href="#' + label + '">here</a>')
			
		elif tag.startswith('<rp ') and tag.endswith('>'): # My definition of a page reference
			label = tag[4:-1]
			if format == 'latex': return latex('\\cpageref{' + label + '}')
			elif format[0:4] == 'html': return html('<a href="#' + label + '">here</a>')
	
	
	# If translating to LaTeX, beginning a paragraph with '<' will cause 
	# '\noindent{}' to be output first.
	elif key == 'Para':
		try:
			if value[0]['t'] == 'Str' and value[0]['c'] == '<' and value[1]['t'] == 'Space': 
				if format == 'latex': return Para([latex('\\noindent{}')] + value[2:])
				elif format[0:4] == 'html': return [Plain([html('<div class="noindent"></div>')]), Para(value[2:])]
				else: return Para(value[2:])
		except: pass # May happen if the paragraph is empty.
	
	
	# Check for tikz CodeBlock. If it exists, try typesetting figure
	elif key == 'CodeBlock':
		(id, classes, attributes), code = value
		if 'tikz' in classes or '\\begin{tikzpicture}' in code:
			outfile = path.join(IMAGE_PATH, my_sha1(code))
			if format[0:4] == 'html': filetype = 'png'
			if format == 'latex': filetype = 'pdf'
			else: filetype = 'png'
			sourceFile = outfile + '.' + filetype
			caption = ''
			id = ''
			library = ''
			for a, b in attributes:
				if a == 'caption': caption = b
				elif a == 'id': id = '{#' + b + '}'
				elif a == 'tikzlibrary': library = b
			if not path.isfile(sourceFile):
				try:
					mkdir(IMAGE_PATH)
					stderr.write('Created directory ' + IMAGE_PATH + '\n')
				except OSError: pass
				tikz2image(code, filetype, outfile, library)
				stderr.write('Created image ' + sourceFile + '\n')
			if id:
				return Para([Image([Str(caption)], [sourceFile, caption]), Str(id)])
			else:
				return Para([Image([Str(caption)], [sourceFile, caption])])
	
	
	# Finally, if we're not in draft mode and we're reading a block comment or 
	# an inline comment or margin note, then suppress output.
	elif '<!comment>' in BLOCK_STATUS and not draft and format != 'revealjs': return []
	elif '<comment>' in INLINE_STATUS and not draft: return []
	elif '<margin>' in INLINE_STATUS and not draft: return []


if __name__ == "__main__":
  toJSONFilter(handle_comments)
