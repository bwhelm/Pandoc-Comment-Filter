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

`<!comment>`: begin comment block (or speaker notes for revealjs)
`</!comment>`: end comment block (or speaker notes for revealjs)
`<!highlight>`: begin highlight block
`</!highlight>`: end highlight block
`<center>`: begin centering
`</center>`: end centering


## Inline Items:

`<comment>`: begin commenting
`</comment>`: end commenting
`<highlight>`: begin highlighting
`</highlight>`: end highlighting
`<fixme>`: begin FixMe margin note (and highlighting)
`</fixme>`: end FixMe margin note (and highlighting)
`<margin>`: begin margin note
`</margin>`: end margin note

'''

from pandocfilters import toJSONFilter, RawInline, Para, Plain

BLOCK_STATUS = []
INLINE_STATUS = []

colors = {
	'<!comment>': 'red', 
	'<comment>': 'red', 
	'<!highlight>': 'magenta', 
	'<highlight>': 'magenta',
	'<margin>': 'red',
	'<fixme>': 'cyan',
}
endColor = '\\color{black}{}'
marginStyle = 'max-width:20%; border: 1px solid black; padding: 1ex; margin: 1ex; float:right; font-size: small;' # HTML style for margin notes

latexText = {
	'<!comment>': '\\color{' + colors['<!comment>'] + '}{}',
	'</!comment>': endColor,
	'<!highlight>': '\\color{' + colors['<!highlight>'] + '}{}',
	'</!highlight>': endColor,
	'<comment>': '\\color{' + colors['<comment>'] + '}{}',
	'</comment>': endColor,
	'<highlight>': '\\color{' + colors['<highlight>'] + '}{}',
	'</highlight>': endColor,
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
	'<!highlight>': '<div style="color: ' + colors['<!highlight>'] + ';">',
	'</!highlight>': '</div>',
	'<comment>': '<span style="color: ' + colors['<comment>'] + ';">',
	'</comment>': '</span>',
	'<highlight>': '<span style="color: ' + colors['<highlight>'] + ';">',
	'</highlight>': '</span>',
	'<margin>': '<span style="color: ' + colors['<margin>'] + '; ' + marginStyle + '">',
	'</margin>': '</span>',
	'<fixme>': '<span style="color: ' + colors['<fixme>'] + '; ' + marginStyle + '">Fix this!</span><span style="color: ' + colors['<fixme>'] + ';">',
	'</fixme>': '</span>',
	'<center>': '<center>', # TODO for html5, need something like: '<div text-align:center;>'
	'</center>': '</center>' # TODO for html5, need something like: '</div>'
}
revealjsText = { # TODO Fill this out where needed!
	'<!comment>': '<aside class="notes">',
	'</!comment>': '</aside>',
	'<!highlight>': '',
	'</!highlight>': '',
	'<comment>': '',
	'</comment>': '',
	'<highlight>': '',
	'</highlight>': '',
	'<margin>': '',
	'</margin>': '',
	'<fixme>': '',
	'</fixme>': '',
	'<center>': '',
	'</center>': ''
}

def latex(text):
	return RawInline('latex', text)

def html(text):
	return RawInline('html', text)
	
def closeHtmlSpan(oldInlineStatus):
	if oldInlineStatus in ['<comment>', '<highlight>', '<fixme>']: return '</span>'
	else: return ''

def closeHtmlDiv(oldBlockStatus):
	if oldBlockStatus in ['<!comment>', '<!highlight>']: return '</div>'
	else: return ''

def handle_comments(key, value, format, meta):
	global BLOCK_STATUS, INLINE_STATUS
	
	# If translating to markdown, leave everything alone.
	if format == 'markdown': return
	
	# Get draft status from metadata field (or assume not draft if there's no such field)
	try: draft = meta['draft']['c']
	except KeyError: draft = False

	# First check to see if we're changing BLOCK_STATUS...
	if key == 'RawBlock':
		type, tag = value
		if type != 'html': pass
		tag = tag.lower()
		if tag in ['<!comment>', '<!highlight>', '<center>']:
			BLOCK_STATUS.append(tag)
			if not draft and format != 'revealjs' and tag != '<center>': return []
			elif format == 'latex':
				return Para([latex(latexText[tag])])
			elif format == 'html' or (format == 'revealjs' and tag == '<!highlight>'):
				return Plain([html(htmlText[tag])])
			elif format == 'revealjs': # tag == '<!comment>', so make speaker note
				return Plain([html(revealjsText[tag])])
			else: return []
			
		elif tag in ['</!comment>', '</!highlight>', '</center>']:
			currentBlockStatus = BLOCK_STATUS.pop()
			if currentBlockStatus[1:] == tag[2:]: # If we have a matching closing tag...
				if not draft and tag != '</center>': return []
				if format == 'latex':
					if BLOCK_STATUS: tag = BLOCK_STATUS[-1] # Switch back to previous
					return Para([latex(latexText[tag])])
				elif format == 'html' or (format == 'revealjs' and tag == '<!highlight>'):
					return Plain([html(htmlText[tag])])
				elif format == 'revealjs':
					return Plain([html(revealjsText[tag])])
				else: return []
			else: exit(1) # TODO Is this right?
			
	# Then check to see if we're changing INLINE_STATUS...
	elif key == 'RawInline':
		type, tag = value
		if type != 'html': pass
		tag = tag.lower()
		
		if tag in ['<margin>', '<comment>', '<highlight>', '<fixme>']:
			INLINE_STATUS.append(tag)
			if not draft: return []
			elif format in ['latex', 'beamer']:
				return latex(latexText[tag])
			elif format in ['html', 'revealjs']:
				return html(htmlText[tag])
			else: return []
		
		elif tag in ['</margin>', '</comment>', '</highlight>', '</fixme>']:
			currentInlineStatus = INLINE_STATUS.pop()
			if currentInlineStatus[1:] == tag[2:]: # If we have a matching closing tag...
				if not draft: return []
				if format in ['latex', 'beamer']:
					if INLINE_STATUS: # Need to switch back to previous inline ...
						if INLINE_STATUS[-1] == '<margin>': newText = latexText['<comment>'] # TODO Need to find a more general solution that works for `<fixme>` as well.
						else: newText = latexText[INLINE_STATUS[-1]]
						if tag == '</margin>': newText = latexText[tag] + newText # Need to close the margin environment before switching back
					elif BLOCK_STATUS: 
						newText = latexText[BLOCK_STATUS[-1]] # ... or to previous block
						if tag == '</margin>': newText = latexText[tag] + newText # Need to close the margin environment before switching back
					else: newText = latexText[tag]
					return latex(newText)
				elif format in ['html', 'revealjs']: return html(htmlText[tag])
			else: exit(1) # TODO Is this right?
			
	
	# Finally, if we're not in draft mode and we're reading a block comment or 
	# an inline comment or margin note, then suppress output.
	elif '<!comment>' in BLOCK_STATUS and not draft and format != 'revealjs': return []
	elif '<comment>' in INLINE_STATUS and not draft: return []
	elif '<margin>' in INLINE_STATUS and not draft: return[]


if __name__ == "__main__":
  toJSONFilter(handle_comments)
