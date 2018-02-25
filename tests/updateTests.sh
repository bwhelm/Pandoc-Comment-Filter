#!/bin/bash
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=draft -M fixme=draft -M margin=draft -M highlight=draft -o tests/spec-draft.markdown
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=draft -M fixme=draft -M margin=draft -M highlight=draft -o tests/spec-draft.latex
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=draft -M fixme=draft -M margin=draft -M highlight=draft -o tests/spec-draft.html4 -t html4
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=draft -M fixme=draft -M margin=draft -M highlight=draft -o tests/spec-draft.html5 -t html5

pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=print -M fixme=print -M margin=print -M highlight=print -o tests/spec-print.markdown
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=print -M fixme=print -M margin=print -M highlight=print -o tests/spec-print.latex
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=print -M fixme=print -M margin=print -M highlight=print -o tests/spec-print.html4 -t html4
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=print -M fixme=print -M margin=print -M highlight=print -o tests/spec-print.html5 -t html5

pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=hide -M fixme=hide -M margin=hide -M highlight=hide -o tests/spec-hide.markdown
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=hide -M fixme=hide -M margin=hide -M highlight=hide -o tests/spec-hide.latex
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=hide -M fixme=hide -M margin=hide -M highlight=hide -o tests/spec-hide.html4 -t html4
pandoc spec.md --lua-filter ./pandocCommentFilter.lua --mathjax -M comment=hide -M fixme=hide -M margin=hide -M highlight=hide -o tests/spec-hide.html5 -t html5
