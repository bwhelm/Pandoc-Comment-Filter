---
title: Pandoc Comment Filter
author: bwhelm
draft: true
...

This is a Pandoc filter to extend the use of RawInline and RawBlocks to
highlight or comment on text, as well as to create margin notes and "Fix
ref!" tags. In draft mode, all comment types are displayed in various
distinguishing colors; in non-draft mode, only highlights are displayed,
and that only in black.

Try setting the `draft` YAML option is set to either `true` or `false`
and then exporting this README to .html, .tex, or .pdf  to see the
effect it has on the final output.


# Syntax for markdown:

## Block Elements: 

Use `<!comment>` or `<!highlight>` to begin block, and `</!comment>` and 
`</!highlight>` to end. These must be in a line on their own, separated 
both above and below by blank lines. Tags may be nested, but the filter 
will break if they are not nested properly.


### Example

Here is normal text.

<!comment>

This commented text will appear in red in draft versions, but will not
appear in non-draft versions.

- Bulleted lists work just fine. 
- So do numbered lists, etc.

<!highlight>

This highlighted text will appear in magenta in draft mode, but in
standard black in non-draft versions.

</!highlight>

Back to commented text (in red).

</!comment>

Now we are back to normal text.

## Inline Elements:

Use `<comment>` or `<highlight>` or `<fixme>` or `<margin>` to begin, and 
`</comment>`, etc.\ to end inline comments. Again, these can be nested, but 
the filter will fail if they are not nested properly.

**NOTE:** github's version of markdown does not display the custom
inline comment markup. To see the syntax of inline examples, you need to
look at the raw version of this README.

### Examples

Here is some example text complete with <highlight>highlighted text (in 
magenta)</highlight> <comment>and with commented text (in 
red)</comment>.<margin>This is a margin note (in red).</margin> For details 
of pandoc's version of markdown syntax, see <fixme>[this 
link](http://pandoc.org)</fixme>.

Note that block elements and inline elements can be combined, and that
other markdown syntax can be used within all comment types as follows.

<!comment>

This is commented text.<margin>And here is a `margin` note, with 
*emphasis*. Marginal notes can also contain <highlight>highlighted 
text</highlight> and back to normal margin color.</margin> This is 
<highlight>highlighted and *italic*</highlight> text. But now should be 
back to commented text.

</!comment>

And now back to normal once again.
