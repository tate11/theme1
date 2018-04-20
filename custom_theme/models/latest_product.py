# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class latest_product(models.Model):
    _name = 'latest.product'
    _rec_name = 'sequence'
     
    name = fields.Char("Name")
    sequence = fields.Integer("Sequence")
    product = fields.Many2one('product.template', 'Product')


class Partner(models.Model):
	_inherit = 'res.partner'

	last_name = fields.Char("Last Name")

	def unlink(self):
		return super(Partner, self).unlink()
