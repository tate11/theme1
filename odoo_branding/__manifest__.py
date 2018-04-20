# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Branding Odoo',
    'version': '1.1',
    'category': '',
    'sequence': 75,
    'author': 'MPTechnolabs',
    'summary': '',
    'description': """

    """,
    'website': '',
    'images': [
    ],
    'depends': [
    	'base',
    	'web',
    	'website',
    	'web_settings_dashboard',
    	'mail',
    ],
    'data': [
    	'views/website_call.xml',
    	'views/company_logo.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
    	'static/src/xml/*.xml',
    ],
}
