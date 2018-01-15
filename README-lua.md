---
title: Pandoc Comment Filter
author: bwhelm
draft: true
...

**NOTE:** github's version of markdown does not display the custom markup
this filter makes possible. To see the syntax of inline examples, you need
to look at the raw version of this README.

This is a Pandoc filter to extend the use of fenced divs and bracketed spans to
highlight or comment on text, as well as to create margin notes and "Fix me!"
tags, create TikZ images from fenced code blocks, and allow for macro
substitution. In draft mode, all comment types are displayed in various
distinguishing colors; in non-draft mode, only highlights and boxes are
displayed, and that only in black. TikZ images and macros will work whether in
draft mode or not.

Try setting the `draft` YAML option to either `true` or `false` and then
exporting this README to .html, .tex, or .pdf to see the effect it has on
the final output.

# Comment Syntax for Markdown

## Block Elements

Use `::: comment` and `::: box` to begin a block, and `:::` to end either one.
These must be in a line on their own. Blocks may be nested, but the filter will
break if they are not nested properly.

### Examples

Here is normal text.

::: comment

This commented text will appear in red in draft versions, but will not
appear in non-draft versions.

- Bulleted lists work just fine.
- So do numbered lists, etc.

< Still in commented text, but this time with non-indented paragraph.

::: box

Now we have some boxed text (still commented). Because it is still
commented, it will show up in draft mode but not at all in non-draft
versions. FIXME: NOTE THAT IT DOES NOT SHOW UP IN RED!

:::

This is the last line of commented text.

:::

Now we are back to normal text.

::: box

This boxed text will show up in plain black in both draft and non-draft
versions.

:::

## Inline Elements

Use `[ ... ]{.INLINE}` with `comment`, `highlight`, `fixme`, or `margin`
substituting for `"INLINE"`.

### Examples

Here is some example text complete with [highlighted text (with yellow
background)]{.highlight} [and with *commented* text (in
red)]{.comment}.[This is a margin note (in red).]{.margin} For details of
pandoc's version of markdown syntax, see [[this
link](http://pandoc.org)]{.fixme}.

Note that block elements and inline elements can be combined, and that
other markdown syntax can be used within all comment types as follows.

::: comment

This is commented text.[And here is a `margin` note, with *emphasis*.
Marginal notes can also contain [highlighted text]{.highlight} and back to
normal margin color.]{.margin} This is [highlighted and
*italic*]{.highlight} text. But now should be back to commented text.

:::

And now back to normal once again.

# TikZ Images

Allow for TikZ figures in code blocks. They should have the following format:

    ~~~ {#fig:id .tikz caption='My *great* caption' title='The title' tikzlibrary='items,to,go,in,\\usetikzlibrary{}'}

    [LaTeX code]

    ~~~

Note that the caption can be formatted text in markdown, but cannot use any
elements from this comment filter.

## Example

For an example, see [fig:something]{.r}.

~~~ {#fig:something .tikz tikzlibrary='calc,intersections,through,backgrounds' caption="Diagram for a proof of Euclid. (Taken from the *TikZ & PGF Manual*, Part\ I, Chapter\ 4.)" title="This is my great title" width=60%}

\begin{tikzpicture}[thick,help lines/.style={thin,draw=black!50}]

\def\A{\textcolor{input}{$A$}}
\def\B{\textcolor{input}{$B$}}
\def\C{\textcolor{output}{$C$}}
\def\D{$D$}
\def\E{$E$}

\colorlet{input}{blue!80!black}
\colorlet{triangle}{orange}
\colorlet{output}{red!70!black}

\coordinate [label=left:\A] (A) at ($ (0,0) + .1*(rand,rand) $);
\coordinate [label=right:\B] (B) at ($ (1.25,0.25) + .1*(rand,rand) $);

\draw [input] (A) -- (B);

\node [name path=D,help lines,draw,label=left:\D] (D) at (A) [circle through=(B)] {};

\node [name path=E,help lines,draw,label=right:\E] (E) at (B) [circle through=(A)] {};

\path [name intersections={of=D and E,by={[label=above:\C]C}}];

\draw [output] (A) -- (C) -- (B);

\foreach \point in {A,B,C}
    \fill [black,opacity=.5] (\point) circle (2pt);

\begin{pgfonlayer}{background}
    \fill[triangle!80] (A) -- (C) -- (B) -- cycle;
\end{pgfonlayer}

\end{tikzpicture}

~~~

# Macros

Here the Comment Filter abuses math environments to create easy macros.

1. In YAML header, specify macros as follows:

        macros:
        - first: this is the substituted text
          second: this is more substituted text

2. Then in text, have users specify macros to be substituted as follows:

        This is my text and $first$. This is more text and $second$.

< As long as the macro labels are not identical to any actual math the user would
use, there should be no problem.
