# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011-TODAY MINORISA (http://www.minorisa.net)
#                             All Rights Reserved.
#                             Minorisa <contact@minorisa.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import glob
import logging
import os
import shutil
import tempfile
import subprocess

from jinja2 import Template
from path import path
from sphinx.application import Sphinx

from openerp import models, fields, api, _, conf
from openerp.modules.graph import Graph

_logger = logging.getLogger(__name__)

BUILD_LANG = [
    ('es', _('Spanish'))
]

BUILD_FMT = [
    ('html', 'HTML')
]


class WizardDoDoc(models.TransientModel):
    _name = 'innubo.doc.wizard.doc'

    _sphinx_app = None
    _doc_path = False
    _doc_url = False
    _template = False
    _build_folder = False
    _output_folder = False
    _modules = []

    build_lang = fields.Selection(string="Lang", required=True, default='es',
                                  selection=BUILD_LANG)
    build_fmt = fields.Selection(string="Format", required=True, default='html',
                                 selection=BUILD_FMT)

    @api.multi
    def do_build(self):
        self.ensure_one()
        # self.get_config_values()
        self._doc_path = os.path.join(tempfile.mkdtemp(), 'innubo_doc')
        self._doc_url = 'https://bitbucket.org/trytonspain/trytond-doc'
        self._template = os.path.join(os.path.dirname(__file__), 'conf.py.template')
        self._build_folder = tempfile.mkdtemp()
        self._output_folder = os.path.join(os.path.dirname(__file__), 'build', 'html')
        _logger.info(self._build_folder)
        self.update_odoo_doc()
        self.fill_build_content()
        self.make_doc()

    def get_config_values(self):
        # TODO ConfigParser, read paths and modules from modules.cfg
        pass

    def update_odoo_doc(self):
        src_dir = '/home/jaume.planas/customer_docs/odoodoc_doc/'
        trg_dir = self._doc_path
        subprocess.check_output(['rsync', '-r', '--del', src_dir, trg_dir])

    def get_documentation_modules(self):
        modules = self.env['ir.module.module'].search([('state', '=', 'installed')])
        graph = Graph()
        graph.add_modules(self._cr, [m.name for m in modules])
        return [m.name for m in graph]

    def build_config_file(self):
        with open(self._template) as f:
            template = Template(f.read())
        config_file = os.path.join(self._build_folder, 'conf.py')
        with open(config_file, 'w') as f:
            f.write(template.render(**self.get_config_template_context()))

    def get_config_template_context(self):
        return {
            'PROJECT': 'Innubo',
            'VERSION': '%s.%s' % (1, 0),
            'INSTALLED_MODULES': self.get_documentation_modules(),
        }

    def fill_build_content(self):
        self.create_symlinks(self._doc_path)
        for module_dir in conf.addons_paths:
            self.create_symlinks(module_dir)
        index = os.path.join(self._doc_path, 'index.rst')
        link = os.path.join(self._build_folder, 'index.rst')
        self.make_link(index, link)
        local_dir = os.path.dirname(__file__)
        build_dir_extensions = os.path.join(self._build_folder, '_extensions')
        if os.path.exists(build_dir_extensions):
            shutil.rmtree(build_dir_extensions)
        shutil.copytree(
            os.path.join(local_dir, '_extensions'),
            build_dir_extensions
        )
        build_dir_static = os.path.join(self._build_folder, '_static')
        if os.path.exists(build_dir_static):
            shutil.rmtree(build_dir_static)
        shutil.copytree(
            os.path.join(local_dir, '_static'),
            build_dir_static
        )

    def create_symlinks(self, origin):
        for module_doc_dir in glob.glob('%s/*/doc/%s' % (origin, self.build_lang)):
            module_name = str(path(module_doc_dir).parent.parent.basename())
            symlink = path(self._build_folder).joinpath(module_name)
            if not symlink.exists():
                path(self._build_folder).relpathto(
                    path(module_doc_dir)).symlink(symlink)

    def make_link(self, origin, destination):
        directory = os.path.dirname(destination)
        if not os.path.exists(destination):
            path(directory).relpathto(path(origin)).symlink(destination)

    def make_doc(self):
        dest = self._output_folder
        doctree_dir = os.path.join(dest, '.doctrees')
        self.build_config_file()
        # We must cache sphinx instance otherwise extensions are loaded
        # multiple times and duplicated references errors are raised.
        if self._sphinx_app is None:
            self._sphinx_app = Sphinx(
                self._build_folder, self._build_folder, dest, doctree_dir, 'html')
        self._sphinx_app.build(force_all=True)
