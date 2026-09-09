import coveralls

master_doc = 'index'
source_suffix = '.rst'
pygments_style = 'sphinx'

templates_path = ['_templates']
exclude_patterns: list[str] = []

todo_include_todos = True
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.imgmath',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

project = 'coveralls-python'
globals()['copyright'] = '2013, TheKevJames'
author = 'TheKevJames'
language = 'en'

version = coveralls.__version__
release = coveralls.__version__
