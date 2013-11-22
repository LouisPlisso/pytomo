==========
README.txt
==========
Author: Ana Oprea
Date: 23.10.2012

Instructions on how to build the html documentation using Sphinx.

Necessary software: Sphinx (http://pypi.python.org/pypi/Sphinx)

Using the .rst files in this folder (apidoc_sphinx_rst), you just need to build
the html documentation:
    user@host:~/Pytomo-1.9.8/apidoc_sphinx_rst$ make html

Delete the existing documentation files (pay attention on your location in the
file system when performing this operation!):
    user@host:~/Pytomo-1.9.8/apidoc_sphinx_rst$ rm -rf ../templates/doc

Copy the html files in the templates/doc folder to be displayed by the web server:
    user@host:~/Pytomo-1.9.8/apidoc_sphinx_rst$ cp -r _build/html/ ../templates/doc

The steps above assume the project structure is the same as the one at the date
mentioned above. If there has been a change (files added/deleted), you should
recreate the .rst files that Sphinx uses to create the html doc.
    user@host:~$ sphinx-apidoc -o Pytomo-1.9.8/apidoc_sphinx_rst Pytomo-1.9.8

The example below shows all the steps followed to create the .rst files,
config.py and the Makefiles. If you redo them, make sure you modify the elements
marked between ** to match the ones below.

===========================================================================
Complete example for Pytomo-1.9.8, including the creation of the .rst files
===========================================================================
user@host:~/test_pytomo_doc$ sphinx-apidoc -o Pytomo-1.9.8/apidoc_sphinx_rst Pytomo-1.9.8
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/setup.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/setup_windows.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/start_crawl.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/start_server.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.dns.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.dns.rdtypes.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.dns.rdtypes.ANY.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.dns.rdtypes.IN.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.flvlib.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.flvlib.scripts.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.kaa_metadata.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.kaa_metadata.audio.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.kaa_metadata.image.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.kaa_metadata.misc.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.kaa_metadata.video.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.rrdtool_win_x86_DLLs.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.web.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.web.contrib.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/pytomo.web.wsgiserver.rst.
Creating file Pytomo-1.9.8/apidoc_sphinx_rst/modules.rst.

user@host:~/test_pytomo_doc$ cd Pytomo-1.9.8/apidoc_sphinx_rst/
user@host:~/test_pytomo_doc/Pytomo-1.9.8/apidoc_sphinx_rst$ sphinx-quickstart
Welcome to the Sphinx 1.1.3 quickstart utility.

Please enter values for the following settings (just press Enter to
accept a default value, if one is given in brackets).

Enter the root path for documentation.
> Root path for the documentation [.]: 

You have two options for placing the build directory for Sphinx output.
Either, you use a directory "_build" within the root path, or you separate
"source" and "build" directories within the root path.
> Separate source and build directories (y/N) [n]: 

Inside the root directory, two more directories will be created; "_templates"
for custom HTML templates and "_static" for custom stylesheets and other static
files. You can enter another prefix (such as ".") to replace the underscore.
> Name prefix for templates and static dir [_]: 

The project name will occur in several places in the built documentation.
> Project name: Pytomo
> Author name(s): Louis Plissoneau

Sphinx has the notion of a "version" and a "release" for the
software. Each version can have multiple releases. For example, for
Python the version is something like 2.5 or 3.0, while the release is
something like 2.5.1 or 3.0a1.  If you don't need this dual structure,
just set both to the same value.
> Project version: 1.9.7
> Project release [1.9.7]: 

The file name suffix for source files. Commonly, this is either ".txt"
or ".rst".  Only files with this suffix are considered documents.
> Source file suffix [.rst]: 

One document is special in that it is considered the top node of the
"contents tree", that is, it is the root of the hierarchical structure
of the documents. Normally, this is "index", but if your "index"
document is a custom template, you can also set this to another filename.
> Name of your master document (without suffix) [index]: 

Sphinx can also add configuration for epub output:
> Do you want to use the epub builder (y/N) [n]: 

Please indicate if you want to use one of the following Sphinx extensions:
********************************************************************
> autodoc: automatically insert docstrings from modules (y/N) [n]: y
********************************************************************
> doctest: automatically test code snippets in doctest blocks (y/N) [n]: 
> intersphinx: link between Sphinx documentation of different projects (y/N) [n]: y
> todo: write "todo" entries that can be shown or hidden on build (y/N) [n]: 
> coverage: checks for documentation coverage (y/N) [n]: 
> pngmath: include math, rendered as PNG images (y/N) [n]: 
> mathjax: include math, rendered in the browser by MathJax (y/N) [n]: 
> ifconfig: conditional inclusion of content based on config values (y/N) [n]: 
**************************************************************************************
> viewcode: include links to the source code of documented Python objects (y/N) [n]: y
**************************************************************************************

A Makefile and a Windows command file can be generated for you so that you
only have to run e.g. `make html' instead of invoking sphinx-build
directly.
> Create Makefile? (Y/n) [y]: 
> Create Windows command file? (Y/n) [y]: 

Creating file ./conf.py.
Creating file ./index.rst.
Creating file ./Makefile.
Creating file ./make.bat.

Finished: An initial directory structure has been created.

You should now populate your master file ./index.rst and create other documentation
source files. Use the Makefile to build the docs, like so:
   make builder
where "builder" is one of the supported builders, e.g. html, latex or linkcheck.

user@host:~/test_pytomo_doc/Pytomo-1.9.8/apidoc_sphinx_rst$ cat conf.py
# -*- coding: utf-8 -*-
#
# Pytomo documentation build configuration file, created by
# sphinx-quickstart on Tue Oct 23 15:09:42 2012.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.insert(0, os.path.abspath('.'))
********************************************************************************
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../pytomo'))
********************************************************************************

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
********************************************************************************
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx',
              'sphinx.ext.viewcode']
********************************************************************************

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Pytomo'
copyright = u'2012, Louis Plissoneau'

******************************************************************************
from setup import VERSION
# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = VERSION
# The full version, including alpha/beta/rc tags.
release = VERSION
******************************************************************************

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'Pytomodoc'


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'Pytomo.tex', u'Pytomo Documentation',
   u'Louis Plissoneau', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'pytomo', u'Pytomo Documentation',
     [u'Louis Plissoneau'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'Pytomo', u'Pytomo Documentation',
   u'Louis Plissoneau', 'Pytomo', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'http://docs.python.org/': None}

user@host:~/test_pytomo_doc/Pytomo-1.9.8/apidoc_sphinx_rst$ cat index.rst
.. Pytomo documentation master file, created by
   sphinx-quickstart on Tue Oct 23 15:09:42 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pytomo's documentation!
==================================

Contents:

.. toctree::
   :maxdepth: 2

********************************************************************************
   modules
********************************************************************************

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

********************************************************************************
!!! when running from here, it won't create doc for pytomo/as_matching.py !!!
=> modify relative path of files in lines 82-83
    def construct_ip_map(goo_file='../pytomo/as_list_goo.txt',                                                                                  
                         you_eu_file='../pytomo/as_list_you_eu.txt'):
********************************************************************************

user@host:~/test_pytomo_doc/Pytomo-1.9.8/apidoc_sphinx_rst$ make html
[...]
looking for now-outdated files... none found
pickling environment... done
checking consistency... done
preparing documents... done
writing output... [100%] pytomo.web.wsgiserver                                                                                                               
writing additional files... genindex py-modindex search
copying static files... done
dumping search index... done
dumping object inventory... done
build succeeded, 91 warnings.

Build finished. The HTML pages are in _build/html.

user@host:~/test_pytomo_doc/Pytomo-1.9.8/apidoc_sphinx_rst$ ll _build/html/
total 1512
-rw-r--r-- 1 user user 220957 Oct 23 15:21 genindex.html
-rw-r--r-- 1 user user   5133 Oct 23 15:21 index.html
-rw-r--r-- 1 user user  21144 Oct 23 15:21 modules.html
-rw-r--r-- 1 user user  15532 Oct 23 15:21 objects.inv
-rw-r--r-- 1 user user  38216 Oct 23 15:21 py-modindex.html
-rw-r--r-- 1 user user 218583 Oct 23 15:12 pytomo.dns.html
-rw-r--r-- 1 user user  34251 Oct 23 15:21 pytomo.dns.rdtypes.ANY.html
-rw-r--r-- 1 user user  44315 Oct 23 15:21 pytomo.dns.rdtypes.html
-rw-r--r-- 1 user user  43226 Oct 23 15:12 pytomo.dns.rdtypes.IN.html
-rw-r--r-- 1 user user  40091 Oct 23 15:12 pytomo.flvlib.html
-rw-r--r-- 1 user user   5335 Oct 23 15:12 pytomo.flvlib.scripts.html
-rw-r--r-- 1 user user 231467 Oct 23 15:21 pytomo.html
-rw-r--r-- 1 user user  13905 Oct 23 15:21 pytomo.kaa_metadata.audio.html
-rw-r--r-- 1 user user  25814 Oct 23 15:21 pytomo.kaa_metadata.html
-rw-r--r-- 1 user user  29497 Oct 23 15:21 pytomo.kaa_metadata.image.html
-rw-r--r-- 1 user user   5191 Oct 23 15:12 pytomo.kaa_metadata.misc.html
-rw-r--r-- 1 user user  15539 Oct 23 15:12 pytomo.kaa_metadata.video.html
-rw-r--r-- 1 user user   3924 Oct 23 15:12 pytomo.rrdtool_win_x86_DLLs.html
-rw-r--r-- 1 user user   6413 Oct 23 15:12 pytomo.web.contrib.html
-rw-r--r-- 1 user user 278797 Oct 23 15:21 pytomo.web.html
-rw-r--r-- 1 user user  57623 Oct 23 15:21 pytomo.web.wsgiserver.html
-rw-r--r-- 1 user user   3359 Oct 23 15:21 search.html
-rw-r--r-- 1 user user  82058 Oct 23 15:21 searchindex.js
-rw-r--r-- 1 user user   4163 Oct 23 15:12 setup.html
-rw-r--r-- 1 user user   7616 Oct 23 15:12 setup_windows.html
drwxr-xr-x 2 user user   4096 Oct 23 15:12 _sources
-rw-r--r-- 1 user user   3370 Oct 23 15:12 start_crawl.html
-rw-r--r-- 1 user user   3675 Oct 23 15:12 start_server.html
drwxr-xr-x 2 user user   4096 Oct 23 15:12 _static

user@host:~/test_pytomo_doc/Pytomo-1.9.8/apidoc_sphinx_rst$ cp -r _build/html/ ../templates/doc



