from setuptools import setup, find_packages

install_requires = ['pandocfilters']

setup(
    name="Pandoc-Comment-Filter",
    version="1.0",
    py_modules=['pandocCommentFilter'],
    install_requires=install_requires,
    zip_safe=True,
    entry_points="""
        [console_scripts]
        pandoc-comments=pandocCommentFilter:cli
    """
)
