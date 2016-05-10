#!/opt/local/bin/python

'''
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

~~~ {#tikz caption='My *great* caption' id='fig:id' tikzlibrary='items,to,go,in,\\usetikzlibrary{}'}

[LaTeX code]

~~~

Note that the caption can be formatted text in markdown.

'''


from panflute import toJSONFilter, convert_text, stringify, shell, debug, MetaInlines, RawBlock, CodeBlock, RawInline, Plain, Para, Str, Space, Image
from os import path, mkdir, chdir, getcwd
from shutil import copyfile, rmtree
from sys import getfilesystemencoding
from tempfile import mkdtemp
from hashlib import sha1

IMAGE_PATH = '/Users/bennett/tmp/pandoc/Figures'
DEFAULT_FONT = 'MinionPro'

colors = {
	'<!comment>': 'red', 
	'<comment>': 'red', 
	'<highlight>': 'yellow',
	'<margin>': 'red',
	'<fixme>': 'cyan',
}
marginStyle = 'max-width:20%; border: 1px solid black; padding: 1ex; margin: 1ex; float:right; font-size: small;' # HTML style for margin notes

latexText = {
	'<!comment>': '\\color{' + colors['<!comment>'] + '}{}',
	'</!comment>': '\\color{black}{}',
	'<!box>': '\\medskip\\noindent\\fbox{\\begin{minipage}[t]{0.98\\columnwidth}',
	'</!box>': '\\end{minipage}}\medskip{}',
	'<comment>': '\\color{' + colors['<comment>'] + '}{}',
	'</comment>': '',
	'<highlight>': '\\hl{',
	'</highlight>': '}',
	'<margin>': '\\marginpar{\\footnotesize{\\color{' + colors['<margin>'] + '}{}',
	'</margin>': '}}',
	'<fixme>': '\\marginpar{\\footnotesize{\\color{' + colors['<fixme>'] + '}{}Fix this!}}\\color{' + colors['<fixme>'] + '}{}',
	'</fixme>': '',
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
revealjsText = {
	'<!comment>': '<aside class="notes">',
	'</!comment>': '</aside>',
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

def my_sha1(x):
	return sha1(x.encode(getfilesystemencoding())).hexdigest()

def tikz2image(tikz, filetype, outfile):
	tmpdir = mkdtemp()
	olddir = getcwd()
	chdir(tmpdir)
	f = open('tikz.tex', 'w')
	f.write(tikz)
	f.close()
	p = shell(['pdflatex', 'tikz.tex'])
	chdir(olddir)
	if filetype == 'pdf':
		copyfile(path.join(tmpdir, 'tikz.pdf'), outfile + '.' + filetype)
	else:
		a = shell(['convert', '-density', '300', path.join(tmpdir, 'tikz.pdf'), '-quality', '100', outfile + '.' + filetype])
	rmtree(tmpdir)

def latex(text):
	return RawInline(text, 'latex')

def html(text):
	return RawInline(text, 'html')
	
def closeHtmlSpan(oldInlineStatus):
	if oldInlineStatus in ['<comment>', '<highlight>', '<fixme>']: return '</span>'
	else: return ''

def closeHtmlDiv(oldBlockStatus):
	if oldBlockStatus in ['<!comment>']: return '</div>'
	else: return ''

def prepare(doc):
	doc.inlineTagStack = []
	doc.blockComment = False
	doc.inlineComment = False
	doc.inlineMargin = False
	doc.inlineHighlight = False
	doc.inlineFontColorStack = ['black']

def handle_comments(elem, doc):
	
	# If translating to markdown, leave everything alone.
	if doc.format == 'markdown': return
	
	# Get draft status from metadata field (or assume not draft if there's no such field)
	draft = doc.get_metadata('draft', default=False)
	
	# Check to see if we're starting or closing a Block element
	if isinstance(elem, RawBlock):
		if elem.format != 'html': return
		
		tag = elem.text.lower()
		
		if not draft:
			if doc.blockComment: # Need to suppress output
				if tag == '</!comment>': doc.blockComment = False
				return []
		
		# Not currently suppressing output ...
		
		if tag in ['<!comment>', '<!box>', '<center>', '<!speaker>']:
			if tag == '<!comment>': 
				doc.blockComment = True
				if not draft: return []
			if doc.format == 'latex': return Para(latex(latexText[tag])) # FIXME: What about beamer?
			elif doc.format in ['html', 'html5']: return Plain(html(htmlText[tag]))
			elif doc.format == 'revealjs': return Plain(html(revealjsText[tag]))
			else: return
		elif tag in ['</!comment>', '</!box>', '</center>', '</!speaker>']:
			if doc.inlineTagStack:
				debug('Need to close all inline elements before closing block elements!\n\n' + str(doc.inlineTagStack) + '\n\nbefore\n\n' + tag + '\n\n')
				exit(1)
			if tag == '</!comment>':
				doc.blockComment = False
				if not draft: return []
			if doc.format == 'latex': return Para(latex(latexText[tag])) # FIXME: What about beamer?
			elif doc.format in ['html', 'html5']: return Plain(html(htmlText[tag]))
			elif doc.format == 'revealjs': return Plain(html(revealjsText[tag]))
			else: return
		else: return # TODO Is this the right thing to do?
	
	if not draft and doc.blockComment: 
		return [] # Need to suppress output
	
	# Then check to see if we're changing doc.inlineTagStack...
	if isinstance(elem, RawInline):
		if elem.format != 'html': return
		
		tag = elem.text.lower()
		
		if not draft: # Check to see if need to suppress output
			if doc.inlineComment: # Need to suppress output
				if tag == '</comment>': doc.inlineComment = False
				return []
			elif doc.inlineMargin: # Need to suppress output
				if tag == '</margin>': doc.inlineMargin = False
				return []
		
		# Not currently suppressing output....
		
		if tag in ['<comment>', '<fixme>', '<margin>', '<highlight>', '</comment>', '</fixme>', '</margin>', '</highlight>']:
			if doc.format in ['latex', 'beamer']: # LaTeX gets treated differently than HTML
				preText = ''
				postText = ''
				if doc.inlineHighlight and tag != '</highlight>': # Cannot change colors within highlighting in LaTeX (but don't do anything when closing the highlight tag!)
					preText = latexText['</highlight>']
					postText = latexText['<highlight>']
				if tag in ['<comment>', '<fixme>', '<margin>', '<highlight>']: # If any opening tag
					if tag == '<comment>': 
						doc.inlineComment = True
						if not draft: return[]
						doc.inlineFontColorStack.append(colors[tag])
					elif tag == '<fixme>':
						doc.inlineFontColorStack.append(colors[tag])
					elif tag == '<margin>': 
						doc.inlineMargin = True
						if not draft: return[]
						doc.inlineFontColorStack.append(colors[tag])
					elif tag == '<highlight>': 
						doc.inlineHighlight = True
						doc.inlineFontColorStack.append(doc.inlineFontColorStack[-1])
					doc.inlineTagStack.append(tag)
					if not draft: return [] # Suppress output of the tag
					return latex(preText + latexText[tag] + postText)
				elif tag in ['</comment>', '</fixme>', '</margin>', '</highlight>']:
					if tag == '</comment>': doc.inlineComment = False
					elif tag == '</fixme>': pass
					elif tag == '</margin>': doc.inlineMargin = False
					elif tag == '</highlight>': doc.inlineHighlight = False
					doc.inlineFontColorStack.pop()
					previousColor = doc.inlineFontColorStack[-1]
					currentInlineStatus = doc.inlineTagStack.pop()
					if currentInlineStatus[1:] == tag[2:]: # We have a matching opening tag
						if not draft: return [] # Suppress output of the tag
						return latex(preText + latexText[tag] + '\\color{' + previousColor + '}{}' + postText)
					else: 
						debug('Closing tag (' + tag + ') does not match opening tag (' + currentInlineStatus + ').\n\n')
#						debug(doc.inlineComment, doc.inlineMargin, doc.inlineHighlight, doc.inlineTagStack, doc.inlineFontColorStack, previousColor, previousTag, currentInlineStatus, preText, postText)
						exit(1)
			elif doc.format in ['html', 'html5']:
				if tag == '<highlight>': doc.inlineHighlight = True
				if tag == '</highlight>': doc.inlineHighlight = False
				if not draft: return []
				if tag in ['<comment>', '<fixme>', '<margin>', '<highlight>']:
					doc.inlineTagStack.append(tag)
				else: doc.inlineTagStack.pop()
				return html(htmlText[tag])
			elif doc.format == 'revealjs': 
				if tag == '<highlight>': doc.inlineHighlight = True
				if tag == '</highlight>': doc.inlineHighlight = False
				if not draft: return []
				if tag in ['<comment>', '<fixme>', '<margin>', '<highlight>']:
					doc.inlineTagStack.append(tag)
				else: doc.inlineTagStack.pop()
				return html(revealjsText[tag])
		
		elif not draft and (doc.inlineComment or doc.inlineMargin): return [] # Suppress all output
		
		elif tag.startswith('<i ') and tag.endswith('>'): # Index
			indexText = tag[3:-1]
			if doc.format == 'latex': return latex('\\index{' + indexText + '}')
			else: return []
			
		elif tag.startswith('<l ') and tag.endswith('>'): # My definition of a label
			label = tag[3:-1]
			if doc.format == 'latex': return latex('\\label{' + label + '}')
			elif doc.format in ['html', 'html5']: return html('<a name="' + label + '"></a>')
			
		elif tag.startswith('<r ') and tag.endswith('>'): # My definition of a reference
			label = tag[3:-1]
			if doc.format == 'latex': return latex('\\cref{' + label + '}')
			elif doc.format in ['html', 'html5']: return html('<a href="#' + label + '">here</a>')
			
		elif tag.startswith('<rp ') and tag.endswith('>'): # My definition of a page reference
			label = tag[4:-1]
			if doc.format == 'latex': return latex('\\cpageref{' + label + '}')
			elif doc.format in ['html', 'html5']: return html('<a href="#' + label + '">here</a>')
	
	elif not draft and (doc.inlineComment or doc.inlineMargin): return [] # Suppress all output
			
	# Check some cases at beginnings of paragraphs
	elif isinstance(elem, Para):
		try:
			# If translating to LaTeX, beginning a paragraph with '<'
			# will cause '\noindent{}' to be output first.
			if isinstance(elem.content[0], Str) and elem.content[0].text == '<' and isinstance(elem.content[1], Space):
				if doc.format == 'latex':
					return Para(latex('\\noindent{}'), *elem.content[2:])
				elif doc.format in ['html', 'html5']:
					return Para(html('<div class="noindent">'), *elem.content[2:], html('</div>'))
				else: return Para(*elem.content[2:])

		except: pass # May happen if the paragraph is empty.
	
	
	# Check for tikz CodeBlock. If it exists, try typesetting figure
	elif isinstance(elem, CodeBlock):
		if 'tikz' in elem.classes or '\\begin{tikzpicture}' in elem.text:
			font = doc.get_metadata('fontfamily', default=None)
			if type(font) == MetaInlines: font = stringify(*font.content)
			else: font = DEFAULT_FONT
			outfile = path.join(IMAGE_PATH, my_sha1(elem.text + font))
			if doc.format == 'latex': filetype = 'pdf' # (without '.')
			else: filetype = 'png' # Default extension (without '.')
			sourceFile = outfile + '.' + filetype
			caption = ''
			library = ''
			if 'caption' in elem.attributes: caption = elem.attributes['caption']
			if 'tikzlibrary' in elem.attributes: library = elem.attributes['tikzlibrary']
			if not path.isfile(sourceFile):
				try:
					mkdir(IMAGE_PATH)
					debug('Created directory ' + IMAGE_PATH + '\n\n')
				except OSError: pass
				codeHeader = '\\documentclass{standalone}\n\\usepackage{' + font + '}\n\\usepackage{tikz}\n'
				if library: codeHeader += '\\usetikzlibrary{' + library + '}\n'
				codeHeader += '\\begin{document}\n'
				codeFooter = '\n\\end{document}\n'
				tikz2image(codeHeader + elem.text + codeFooter, filetype, outfile)
				debug('Created image ' + sourceFile + '\n\n')
			if caption: formattedCaption = convert_text(caption)
			else: formattedCaption = Str('')
			return Para(Image(*formattedCaption[0].content, url=sourceFile, title=caption, identifier=elem.identifier, classes=elem.classes, attributes=elem.attributes), Str(str(font)))


if __name__ == "__main__": toJSONFilter(handle_comments, prepare)
