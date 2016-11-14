---
title: Pandoc Comment Filter
author: bwhelm
draft: true
...

**NOTE:** github's version of markdown does not display the custom markup
this filter makes possible. To see the syntax of inline examples, you need
to look at the raw version of this README.

This is a Pandoc filter to extend the use of RawInline and RawBlocks to
highlight or comment on text, as well as to create margin notes and "Fix
me!" tags. In draft mode, all comment types are displayed in various
distinguishing colors; in non-draft mode, only highlights and boxes are
displayed, and that only in black.

Try setting the `draft` YAML option to either `true` or `false` and then
exporting this README to .html, .tex, or .pdf to see the effect it has on
the final output.

# Syntax for markdown:

## Block Elements:

Use `<!comment>` and `<!box>` to begin a block, and `</!comment>` and
`</!box>` to end it. These must be in a line on their own, separated both
above and below by blank lines. Tags may be nested, but the filter will
break if they are not nested properly.

### Examples

Here is normal text.

<!comment>

This commented text will appear in red in draft versions, but will not
appear in non-draft versions.

- Bulleted lists work just fine. 
- So do numbered lists, etc.

< Still in commented text, but this time with non-indented paragraph.

<!box>

Now we have some boxed text (still commented). Because it is still
commented, it will show up in draft mode but not at all in non-draft
versions.

</!box>

</!comment>

Now we are back to normal text.

<!box>

This boxed text will show up in plain black in both draft and non-draft
versions.

</!box>

## Inline Elements:

Use `<comment>` or `<highlight>` or `<fixme>` or `<margin>` to begin, and
`</comment>`, etc.\ to end inline comments. Again, these can be nested,
but the filter will fail if they are not nested properly.

### Examples

Here is some example text complete with [highlighted text (with yellow
background)]{.highlight} [and with *commented* text (in
red)]{.comment}.[This is a margin note (in red).]{.margin} For details of
pandoc's version of markdown syntax, see [[this
link](http://pandoc.org)]{.fixme}.

Note that block elements and inline elements can be combined, and that
other markdown syntax can be used within all comment types as follows.

<!comment>

This is commented text.[And here is a `margin` note, with *emphasis*.
Marginal notes can also contain [highlighted text]{.highlight} and back to
normal margin color.]{.margin} This is [highlighted and
*italic*]{.highlight} text. But now should be back to commented text.

</!comment>

And now back to normal once again.
