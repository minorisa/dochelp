# -*- coding: utf-8 -*-
from __future__ import print_function

"""
    odoodoc
    -------

    :copyright: Copyright 2016 by Minorisa, S.L.
    :license: BSD, see LICENSE for details.
"""

import re
from collections import OrderedDict
from docutils import nodes
from docutils.parsers.rst import directives
from docutils.transforms import Transform
from sphinx.util.compat import Directive
from sphinx import roles

import erppeek

_client = None


def get_field_data(model_name, field_name, show_help, odoo_lang):
    global _client
    if show_help:
        key = 'help'
    else:
        key = 'string'
    ctx = {'lang': odoo_lang}
    try:
        xname = _client.execute(
            model_name,
            'fields_get',
            field_name,
            context=ctx)[field_name][key]
    except:
        xname = None
    return xname


class FieldDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {
        'help': directives.flag,
        'class': directives.class_option,
    }

    def run(self):
        config = self.state.document.settings.env.config
        content = self.arguments[0]
        if 'help' in self.options:
            show_help = True
        else:
            show_help = False

        classes = [config.odoodoc_fieldclass]
        if 'class' in self.options:
            classes.extend(self.options['class'])

        model_name, field_name = content.split('/')

        text = get_field_data(model_name, field_name, show_help, config.odoo_lang)
        if text is None:
            return [self.state_machine.reporter.warning(
                'Model/Field "%s" not found.' % content, line=self.lineno)]
        return [nodes.literal(text=text, classes=classes)]


def get_menu_data(module_name, menu_name, show_name_only, odoo_lang):
    o = _client.IrModelData.read([
        ('module', '=', module_name),
        ('name', '=', menu_name)
    ], limit=1, fields=['res_id'])
    res_id = o and o[0] or False
    if not res_id:
        return None
    menu = _client.IrUiMenu.browse(res_id['res_id'], context={'lang': odoo_lang})
    if show_name_only:
        text = menu.name or None
    else:
        text = menu.complete_name or None
    return text


class MenuDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {
        # Prints only the name of the menu entry instead of its full path
        'nameonly': directives.flag,
        'class': directives.class_option,
    }

    def run(self):
        config = self.state.document.settings.env.config
        content = self.arguments[0]
        if 'nameonly' in self.options:
            show_name_only = True
        else:
            show_name_only = False

        classes = ['menuselection', config.odoodoc_menuclass]
        if 'class' in self.options:
            classes.extend(self.options['class'])

        module_name, menu_name = content.split('/')

        text = get_menu_data(module_name, menu_name, show_name_only, config.odoo_lang)
        if text is None:
            return [self.state_machine.reporter.warning(
                'Menu entry "%s" not found.' % content, line=self.lineno)]
        text = text.replace('/', u' \N{TRIANGULAR BULLET} ')
        return [nodes.inline(text=text, classes=classes)]


class OdooModelFieldList(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'fields': directives.unchanged,
        'class': directives.class_option
    }
    default_fields = []
    global _client

    def run(self):
        config = self.state.document.settings.env.config
        model_name = self.arguments[0]
        optfields = self.options.get('fields')
        if not optfields:
            fields = _client.model(model_name).keys()
        else:
            fields = optfields.split(' ')
        l = [x for x in fields if
             x not in ['create_uid', 'create_date', 'write_uid', 'write_date']]
        res1 = _client.execute(model_name, 'fields_get', l,
                               context={'lang': config.odoo_lang})
        res = OrderedDict()
        print('**************************', model_name)
        for a in l:
            res[a] = res1[a]
        classes = [config.odoodoc_fieldlistclass]
        if 'class' in self.options:
            classes.extend(self.options['class'])
        return [nodes.field_list('', *(
            nodes.field('',
                        nodes.field_name(text=v['string'] or k),
                        nodes.field_body(
                            '',
                            # keep help formatting around (e.g. newlines for lists)
                            nodes.line_block('', *(
                                nodes.line(text=line)
                                for line in v['help'].split('\n')
                            ))
                        )
                        )
            for k, v in res.iteritems()
            # only display if there's a help text
            if v.get('help')
        ), classes=classes, format='html')]


def get_model_data(model_name, odoo_lang):
    global _client
    ctx = {'lang': odoo_lang}
    try:
        xname = _client.IrModel.get([
            ('model', '=', model_name)
        ], context=ctx)
    except:
        xname = None
    return xname


class ModelDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {
        'full': directives.flag,
        'class': directives.class_option,
    }

    def run(self):
        config = self.state.document.settings.env.config
        model_name = self.arguments[0]
        # if 'full' in self.options:
        #     show_help = True
        # else:
        #     show_help = False

        classes = [config.odoodoc_modelclass]
        if 'class' in self.options:
            classes.extend(self.options['class'])

        text = get_model_data(model_name, config.odoo_lang)
        if text is None:
            return [self.state_machine.reporter.warning(
                'Model "%s" not found.' % model_name, line=self.lineno)]
        return [nodes.literal(text=text, classes=classes)]


class References(Transform):
    """
    Parse and transform menu and field references in a document.
    """

    default_priority = 999

    def apply(self):
        config = self.document.settings.env.config
        pattern = config.odoodoc_pattern
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)
        for node in self.document.traverse(nodes.Text):
            parent = node.parent
            if isinstance(parent, (nodes.literal, nodes.FixedTextElement)):
                # ignore inline and block literal text
                continue
            text = unicode(node)
            modified = False

            match = pattern.search(text)
            while match:
                if len(match.groups()) != 1:
                    raise ValueError(
                        'odoodoc_issue_pattern must have '
                        'exactly one group: {0!r}'.format(match.groups()))
                # extract the reference data (excluding the leading dash)
                refdata = match.group(1)
                start = match.start(0)
                end = match.end(0)

                data = refdata.split(':')
                kind = data[0]
                content = data[1]
                if len(data) > 2:
                    options = data[2]
                else:
                    options = None

                if kind == 'field':
                    model_name, field_name = content.split('/')
                    if options == 'help':
                        show_help = True
                    else:
                        show_help = False
                    replacement = get_field_data(model_name, field_name, show_help,
                                                 config.odoo_lang)
                elif kind == 'menu':
                    module_name, menu_name = content.split('/')
                    if options == 'nameonly':
                        show_name_only = True
                    else:
                        show_name_only = False
                    replacement = get_menu_data(module_name, menu_name, show_name_only,
                                                config.odoo_lang)
                else:
                    replacement = refdata

                text = text[:start] + (replacement or u'') + text[end:]
                modified = True

                match = pattern.search(text)

            if modified:
                parent.replace(node, [nodes.Text(text)])


def init_transformer(app):
    global _client
    if app.config.odoodoc_plaintext:
        app.add_transform(References)
    _client = erppeek.Client(app.config.odoo_server,
                             db=app.config.odoo_db,
                             user=app.config.odoo_user,
                             password=app.config.odoo_pwd)


def icon_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    """Font Awesome icon.
    """
    s = u'<i class="fa fa-{}" aria-hidden="true"></i>'.format(text)
    node = nodes.raw('', s, format='html')
    return [node], []


def odoomenu_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    app = inliner.document.settings.env.app
    config = app.config

    module_name, menu_name = text.split('/')
    s = get_menu_data(module_name, menu_name, False, config.odoo_lang)
    s = s.replace('/', '  --> ')
    return roles.menusel_role('menuselection', rawtext, s, lineno, inliner, options,
                              content)


def odoofield_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    app = inliner.document.settings.env.app
    config = app.config

    model_name, field_name = text.split('/')
    s = get_field_data(model_name, field_name, False, config.odoo_lang)
    # node = nodes.inline(rawsource=rawtext, text=s)
    node = nodes.literal(rawsource=rawtext, text=s)
    # node['classes'].append('guilabel')
    return [node], []


def setup(app):
    app.add_config_value('odoo_server', None, 'env')
    app.add_config_value('odoo_db', None, 'env')
    app.add_config_value('odoo_user', None, 'env')
    app.add_config_value('odoo_pwd', None, 'env')
    app.add_config_value('odoo_lang', 'es_ES', 'env')
    app.add_config_value('odoodoc_plaintext', True, 'env')
    app.add_config_value('odoodoc_pattern', re.compile(r'@(.|[^@]+)@'), 'env')
    app.add_config_value('odoodoc_menuclass', 'odoodocmenu', 'env')
    app.add_config_value('odoodoc_fieldclass', 'odoodocfield', 'env')
    app.add_config_value('odoodoc_modelclass', 'odoodocmodel', 'env')
    app.add_config_value('odoodoc_fieldlistclass', 'odoodocfieldlist', 'env')

    app.add_directive('field', FieldDirective)
    app.add_directive('menu', MenuDirective)
    app.add_directive('model', ModelDirective)
    app.add_directive('fields', OdooModelFieldList)

    app.add_role('favicon', icon_role)
    app.add_role('odoomenu', odoomenu_role)
    app.add_role('odoofield', odoofield_role)

    app.connect('builder-inited', init_transformer)
