import os
import subprocess
import nose.tools as nt


def call_pandoc(pandoc_cmd):
    p = subprocess.Popen(pandoc_cmd, stdout=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout.decode()


def _test(format):
    pandoc_cmd = ('pandoc', 'spec.md',
                  '--lua-filter', './pandocCommentFilter.lua',
                  '--mathjax',
                  '-M', 'comment=draft',
                  '-M', 'fixme=draft',
                  '-M', 'margin=draft',
                  '-M', 'highlight=draft',
                  '--to', format,
                  '-o', 'temp.txt')
    call_pandoc(pandoc_cmd)
    with open('temp.txt') as f:
        pandoc_output = f.read()
    ref_file = 'tests/spec-draft.{ext}'.format(ext=format)
    with open(ref_file) as f:
        nt.assert_multi_line_equal(pandoc_output, f.read())

    pandoc_cmd = ('pandoc', 'spec.md',
                  '--lua-filter', './pandocCommentFilter.lua',
                  '--mathjax',
                  '-M', 'comment=print',
                  '-M', 'fixme=print',
                  '-M', 'margin=print',
                  '-M', 'highlight=print',
                  '--to', format,
                  '-o', 'temp.txt')
    call_pandoc(pandoc_cmd)
    with open('temp.txt') as f:
        pandoc_output = f.read()
    ref_file = 'tests/spec-print.{ext}'.format(ext=format)
    with open(ref_file) as f:
        nt.assert_multi_line_equal(pandoc_output, f.read())

    pandoc_cmd = ('pandoc', 'spec.md',
                  '--lua-filter', './pandocCommentFilter.lua',
                  '--mathjax',
                  '-M', 'comment=hide',
                  '-M', 'fixme=hide',
                  '-M', 'margin=hide',
                  '-M', 'highlight=hide',
                  '--to', format,
                  '-o', 'temp.txt')
    call_pandoc(pandoc_cmd)
    with open('temp.txt') as f:
        pandoc_output = f.read()
    ref_file = 'tests/spec-hide.{ext}'.format(ext=format)
    with open(ref_file) as f:
        nt.assert_multi_line_equal(pandoc_output, f.read())

    os.remove('temp.txt')


def test_markdown():
    print("- Markdown")
    _test('markdown')


def test_html4():
    print("- HTML4")
    _test('html4')


def test_html5():
    print("- HTML5")
    _test('html5')


def test_latex():
    print("- LaTeX")
    _test('latex')


def test_all_formats():
    for format in ('markdown', 'latex', 'html', 'html5'):
        _test(format)


if __name__ == '__main__':
    print("Comparing pandoc output with reference output in tests/:")
    test_markdown()
    test_html4()
    test_html5()
    test_latex()
    print("All comparison tests passed ok!")
