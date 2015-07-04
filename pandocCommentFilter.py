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


Syntax Extensions
-----------------

Block-Level Items:

`<!comment>`: begin comment block
`<!highlight>`: begin highlight block
`<!end>`: end comment/highlight blocks
`<center>`: begin centering
`</center>`: end centering


Inline Items:

`<comment>`: begin commenting
`<highlight>`: begin highlighting
`<fixref>`: begin Fix Ref margin note (and highlighting)
`<end>`: end the above (return to black text)
`<margin>`: begin margin note
`</margin>`: end margin note


'''

from pandocfilters import toJSONFilter, RawInline, Para, Plain

blockStatus = '<!end>'
blockColor = 'black'
inlineStatus = '<end>'
colors = {	'<!comment>': 'red', 
			'<comment>': 'red', 
			'<!highlight>': 'magenta', 
			'<highlight>': 'magenta',
			'<margin>': 'red',
			'<fixref>': 'cyan',
			'<!end>': 'black', 
			'<end>': 'black'
			}
marginStyle = 'max-width:20%; border: 1px solid black; padding: 1ex; margin: 1ex; float:right; font-size: small;' # HTML style for margin notes

marginStatus = False # Whether currently in a margin note or not

def latex(text):
	return RawInline('latex', text)

def html(text):
	return RawInline('html', text)
	
def closeHtmlSpan(oldInlineStatus):
	if oldInlineStatus in ['<comment>', '<highlight>', '<fixref>']: return '</span>'
	else: return ''

def closeHtmlDiv(oldBlockStatus):
	if oldBlockStatus in ['<!comment>', '<!highlight>']: return '</div>'
	else: return ''

def handle_comments(key, value, format, meta):
	global blockStatus, blockColor, inlineStatus, marginStatus
	
	# If translating to markdown, leave everything alone.
	if format == 'markdown': return
	
	# Keep track of this for later....
	oldInlineStatus = inlineStatus
	oldBlockStatus = blockStatus

	# Get draft status from metadata field (or assume not draft if there's no such field)
	try: draft = meta['draft']['c']
	except KeyError: draft = False

	# First check to see if we're changing blockStatus...
	if key == 'RawBlock':
		type, tag = value
		tag = tag.lower()
		if type == 'html':
			if tag in ['<!comment>', '<!highlight>']:
				blockStatus = tag
				blockColor = colors[blockStatus]
				if not draft: return []
				elif format == 'latex':
					return Para([latex('\\color{' + blockColor + '}{}')])
				elif format == 'html':
					return Plain([html(closeHtmlDiv(oldBlockStatus) + '<div style="color: ' + blockColor + ';">')])
				else: return []
				
			elif tag == '<!end>':
				blockStatus = tag
				blockColor = colors[blockStatus]
				if not draft: return []
				elif format == 'latex':
					return Para([latex('\\color{' + blockColor + '}{}')])
				elif format == 'html':
					return Plain([html('</div>')])
				else: return []


	# Then check to see if we're changing inlineStatus...
	elif key == 'RawInline':
		type, tag = value
		if type != 'html': pass
		tag = tag.lower()
		
		if tag == '<margin>':
			marginStatus = True
			if not draft: return []
			elif format == 'latex':
				return latex('\\marginpar{\\footnotesize{\\color{' + colors[tag] + '}{}')
			elif format == 'html':
				return html(closeHtmlSpan(oldInlineStatus) + '<span style="color: ' + colors[tag] + '; ' + marginStyle + '">')
			else: return []
		
		elif tag == '<comment>':
			inlineStatus = tag
			if not draft: return [] # If not draft, then ignore
			elif format == 'latex':
				return latex('\\color{' + colors[inlineStatus] + '}{}')
			elif format == 'html': 
				return html(closeHtmlSpan(oldInlineStatus) + '<span style="color: ' + colors[inlineStatus] + ';">')
			else: return []
		
		elif tag == '<fixref>':
			inlineStatus = tag
			if not draft: return[]
			elif format == 'latex':
				return latex('\\marginpar{\\footnotesize{\\color{' + colors[inlineStatus] + '}{}Fix ref!}}\\color{' + colors[inlineStatus] + '}{}')
			elif format == 'html': 
				return html(closeHtmlSpan(oldInlineStatus) + '<span style="color: ' + colors[inlineStatus] + '; ' + marginStyle + '">Fix ref!</span><span style="color: ' + colors[inlineStatus] + ';">')
			else: return []
		
		elif tag == '<highlight>':
			inlineStatus = tag
			if draft:
				if format == 'latex':
					return latex('\\color{' + colors[inlineStatus] + '}{}')
				elif format == 'html': 
					return html(closeHtmlSpan(oldInlineStatus) + '<span style="color: ' + colors[inlineStatus] + ';">')
				else: return []
			else: return []
		
		elif tag == '<end>':
			inlineStatus = tag
			if not draft: return []
			elif format == 'latex': 
				if marginStatus: return latex('\\color{' + colors['<margin>'] + '}{}')
				else: return latex('\\color{' + blockColor + '}{}')
			elif format == 'html': return html('</span>')
		
		elif tag == '</margin>':
			marginStatus = False
			if not draft: return []
			elif format == 'latex': return latex('\\color{' + colors[inlineStatus] + '}}}')
			elif format == 'html': return html('</span>')
		
	# Finally, if we're not in draft mode and we're reading a block comment or 
	# an inline comment or margin note, then suppress output.
	elif blockStatus in ['<!comment>'] and not draft: return []
	elif inlineStatus in ['<comment>'] and not draft: return []
	elif marginStatus and not draft: return[]


if __name__ == "__main__":
  toJSONFilter(handle_comments)
