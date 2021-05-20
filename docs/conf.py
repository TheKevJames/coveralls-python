from coveralls import __version__


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.imgmath',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = 'coveralls-python'
globals()['copyright'] = '2013, TheKevJames'
author = 'TheKevJames'

version = __version__
release = __version__

language = None

exclude_patterns = []

pygments_style = 'sphinx'

todo_include_todos = True
