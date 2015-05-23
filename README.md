---
title: Pandoc Comment Filter
author: bwhelm
draft: true
...

This is a Pandoc filter to extend the use of RawInline and RawBlocks to
highlight or comment on text, as well as to create margin notes and “Fix
ref!” tags. In draft mode, all comment types are displayed in various
distinguishing colors; in non-draft mode, only highlights are displayed,
and that only in black.

Try setting the `draft` YAML option is set to either `true` or `false`
and then exporting this README to .html, .tex, or .pdf  to see the
effect it has on the final output.


# Syntax for markdown:

## Block Elements: 

Use `<!comment>` or `<!highlight>` to begin block, and `<!end>` to end.
These must be in a line on their own, separated both above and below by
blank lines. Tags that begin blocks can be followed by other tags that
begin blocks, but eventually it should be followed by `<!end>`.

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

<!end>

Now we are back to normal text.

## Inline Elements:

Use `<comment>` or `<highlight>` or `<fixref>` or `<margin>` to begin,
and `<end>` to end inline comments. These can be in paragraphs on their
own, or they can be part of an existing paragraph. `<comment>`,
`<highlight>`, and `<fixref>` can be followed by each other (but not by
`<margin>`), but eventually must be followed by `<end>`.

**NOTE:** github’s version of markdown does not display the custom
inline comment markup. To see the syntax of inline examples, you need to
look at the raw version of this README.

### Examples

Here is some example text complete with <highlight>highlighted text (in
magenta)<comment> and with commented text  (in red)<end>.<margin>This is
a margin note (in red).<end> For details of pandoc’s version of markdown
syntax, see <fixref>[this link](http://pandoc.org)<end>.

Note that block elements and inline elements can be combined, and that
other markdown syntax can be used within all comment types as follows.

<!comment>

This is commented text.<margin>And here is a `margin` note, with
*emphasis*.<end> This is <highlight>highlighted and *italic*<end> text.

<!end>

