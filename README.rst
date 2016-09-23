=======================
Odoo Documentation Help
=======================

This module creates both a Help menu option and a Sphinxh-based documentation foundation.

Help Menu
^^^^^^^^^

A new Menu item is created in the top navigation menu bar. This is an URL action,
opening a ``dochelp/index.html`` web page. An Odoo controller for HTML pages located under ths home page is also included.

Sphinx documentation
^^^^^^^^^^^^^^^^^^^^

Help website is created using `Sphinx <http://http://www.sphinx-doc.org/>`_,
a standard tool that makes it easy to create intelligent and beautiful documentation,
that uses `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ as its markup language,
and many of its strengths come from the power and straightforwardness of
reStructuredText and its parsing and translating suite,
the `Docutils <http://docutils.sourceforge.net/>`_.

Usage
^^^^^

The documentation system uses the inheritance modular system
from `sphinxcontrib.inheritance <https://pypi.python.org/pypi/sphinxcontrib-inheritance/>`_.

This addon installs a Wizard enabling you to render the documentation. It uses 2 sources:

* The **odoo-doc** repository in GitHub, containing the source files for the core modules of Odoo.
* All rst files in the non-core installed modules that matches the pattern ``doc\<language>\*.rst``.

The non-core files should follow the inheritance guidelines specified in the ``sphinxcontrib.inheritance``.

Credits
^^^^^^^

Contributors
""""""""""""

* Jaume Planas <jaume.planas@minorisa.net>

Maintainer
""""""""""

.. image:: http://www.minorisa.net/wp-content/themes/minorisa/img/logo-minorisa.png
   :alt: Minorisa, S.L.
   :target: http://www.minorisa.net


