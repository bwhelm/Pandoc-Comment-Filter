---
title: Pandoc Comment Filter Test Spec
author: bwhelm
draft: true
numbersections: true
macros:
- first: This is the *first* macro. [Highlighted.]{.highlight}
  second: This is the **second** macro. [With fixme.]{.fixme}
---

# File Transclusion

@[](transcluded.md)

# Non-Indented Paragraph

- Bulleted list

< Non-indented paragraph.

# Images

## Online Image

![Test caption](https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Aristotle_Altemps_Inv8575.jpg/440px-Aristotle_Altemps_Inv8575.jpg){width=40% -}

FIXME: There are problems with arbitrary filenames in LaTeX.

## TikZ Image

~~~ {#identifier .tikz tikzlibrary="arrows" caption="A caption." title="The title" width=25%}
\begin{tikzpicture}
\draw (0,0) node [shape=circle,draw] {hello};
\end{tikzpicture}
~~~

# Block Elements

Normal text.

::: comment

Commented text (red, only in draft). *Emphasized* and **bold**. [Highlighted.]{.highlight}[Marginal note]{.margin} And a [fixme]{.fixme}.

- Bulleted lists
    1. Numbered lists

< Non-indented paragraph.

::: box

Boxed paragraph. FIXME: NOTE THAT IT DOES NOT SHOW UP IN RED IN LATEX!

:::

Out of box, still commented.

:::

Now back to normal text.

::: box

More boxed text, out of comment. [Commented.]{.comment} [Highlighted.]{.highlight} (Can't put marginal notes or fixmes in boxed text because of LaTeX limitations.)

:::

# Macros

Macro: $first$ Another: $second$

# Inline Elements

Normal [highlighted]{.highlight} [commented]{.comment}.[Marginal note
[highlighted]{.highlight}.]{.margin} [Fixme text [highlighted]{.highlight} [and
commented]{.comment} and normal fixme.]{.fixme} And [Text In Small Caps]{.smcaps}.

FIXME: HIGHLIGHTED TEXT DOES NOT PICK UP TEXT COLOR WHEN NESTED IN HTML! This requires using `<mark style="color: red;"> ... </mark>`.

::: comment

Commented text.[Margin note with *emphasis* and [highlighted text]{.highlight}.
Normal margin.]{.margin} This is [highlighted and *italic*]{.highlight} text.
But now should be back to commented text.

:::

And now back to normal once again. Now testing cross-references and index:

- label: (Nothing appears here.)[label]{.l}
- reference: See [label]{.r}, on [label]{.rp}.
- footnote reference:^[Here.[notelabel]{.l}] See [notelabel]{.r}.
- index: (Nothing appears here.)[index]{.i}

