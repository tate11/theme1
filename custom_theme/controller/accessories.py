# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
from werkzeug.exceptions import Forbidden

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.website.models.website import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website_form.controllers.main import WebsiteForm

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

class Accessories(http.Controller):

	_name = 'accessories'

	def __init__(self):
		self.table = {}

	def _get_search_domain(self, search, category, attrib_values, price_vals = {}):
		domain = request.website.sale_product_domain()
		print"::::::::::::888******:::::::::::", domain, search, category
		if search:
			for srch in search.split(" "):
				domain += [
					'|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
					('description_sale', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]

		if category:
			domain += [('public_categ_ids', 'child_of', int(category))]

		if attrib_values:
			attrib = None
			ids = []
			for value in attrib_values:
				if not attrib:
					attrib = value[0]
					ids.append(value[1])
				elif value[0] == attrib:
					ids.append(value[1])
				else:
					domain += [('attribute_line_ids.value_ids', 'in', ids)]
					attrib = value[0]
					ids = [value[1]]
			if attrib:
				domain += [('attribute_line_ids.value_ids', 'in', ids)]

		return domain

	def _check_place(self, posx, posy, sizex, sizey):
		res = True
		for y in range(sizey):
			for x in range(sizex):
				if posx + x >= PPR:
					res = False
					break
				row = self.table.setdefault(posy + y, {})
				if row.setdefault(posx + x) is not None:
					res = False
					break
			for x in range(PPR):
				self.table[posy + y].setdefault(x, None)
		return res

	def process(self, products, ppg=PPG):
		print '-------------------prcess-----', products, ppg
		# Compute products positions on the grid
		minpos = 0
		index = 0
		maxy = 0
		for p in products:
			print '--QQQQQQQ', p.website_size_x
			x = min(max(p.website_size_x, 1), PPR)
			y = min(max(p.website_size_y, 1), PPR)
			print '----AAAAAAAAAAAAAAA---------', x, y
			if index >= ppg:
				x = y = 1

			pos = minpos
			while not self._check_place(pos % PPR, pos / PPR, x, y):
				pos += 1
			# if 21st products (index 20) and the last line is full (PPR products in it), break
			# (pos + 1.0) / PPR is the line where the product would be inserted
			# maxy is the number of existing lines
			# + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
			# and to force python to not round the division operation
			if index >= ppg and ((pos + 1.0) / PPR) > maxy:
				break

			if x == 1 and y == 1:   # simple heuristic for CPU optimization
				minpos = pos / PPR

			for y2 in range(y):
				for x2 in range(x):
					self.table[(pos / PPR) + y2][(pos % PPR) + x2] = False
			self.table[pos / PPR][pos % PPR] = {
				'product': p, 'x': x, 'y': y,
				'class': " ".join(map(lambda x: x.html_class or '', p.website_style_ids))
			}
			if index <= ppg:
				maxy = max(maxy, y + (pos / PPR))
			index += 1

		# Format table according to HTML needs
		rows = self.table.items()
		rows.sort()
		rows = map(lambda x: x[1], rows)
		for col in range(len(rows)):
			cols = rows[col].items()
			cols.sort()
			x += len(cols)
			rows[col] = [c for c in map(lambda x: x[1], cols) if c]
		print '----rows--------', rows
		return rows

	def _get_search_order(self, post):
		# OrderBy will be parsed in orm and so no direct sql injection
		# id is added to be sure that order is a unique sort key
		res = 'website_published desc,%s , id desc' % post.get('order', 'website_sequence desc')
		return res

	def get_attribute_value_ids(self, product):
		""" list of selectable attributes of a product

		:return: list of product variant description
		   (variant id, [visible attribute ids], variant price, variant sale price)
		"""
		# product attributes with at least two choices
		quantity = product._context.get('quantity') or 1
		product = product.with_context(quantity=quantity)

		visible_attrs_ids = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id').ids
		to_currency = request.website.get_current_pricelist().currency_id
		attribute_value_ids = []
		for variant in product.product_variant_ids:
			if to_currency != product.currency_id:
				price = variant.currency_id.compute(variant.website_public_price, to_currency) / quantity
			else:
				price = variant.website_public_price / quantity
			visible_attribute_ids = [v.id for v in variant.attribute_value_ids if v.attribute_id.id in visible_attrs_ids]
			attribute_value_ids.append([variant.id, visible_attribute_ids, variant.website_price, price])
		return attribute_value_ids

	@http.route([
	'/accessories',
	'/accessories/page/<int:page>',
	], type='http', auth="public", website=True)
	def accessories(self, page=0, category=None, search='', ppg=False, **post):
		print '-------post-------', post
		if ppg:
			try:
				ppg = int(ppg)
			except ValueError:
				ppg = PPG
			post["ppg"] = ppg
		else:
			ppg = PPG

		attrib_list = request.httprequest.args.getlist('attrib')
		attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
		attributes_ids = set([v[0] for v in attrib_values])
		attrib_set = set([v[1] for v in attrib_values])

		domain = self._get_search_domain(search, category, attrib_values)
		print '----domain-------', domain
		keep = QueryURL('/accessories', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))
		pricelist_context = dict(request.env.context)
		if not pricelist_context.get('pricelist'):
			pricelist = request.website.get_current_pricelist()
			pricelist_context['pricelist'] = pricelist.id
		else:
			pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

		request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

		url = "/accessories"
		if search:
			post["search"] = search
		if category:
			category = request.env['product.public.category'].browse(int(category))
			url = "/category/%s" % slug(category)
		if attrib_list:
			post['attrib'] = attrib_list

		categs = request.env['product.public.category'].search([('parent_id', '=', False)])
		Product = request.env['product.template']

		parent_category_ids = []
		if category:
			parent_category_ids = [category.id]
			current_category = category
			while current_category.parent_id:
				parent_category_ids.append(current_category.parent_id.id)
				current_category = current_category.parent_id

		product_count = Product.search_count(domain)
		pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
		print":::::::::::::::::::pager:::::::@@@@@@@@@@@:::::::::::::::::::", pager, product_count, domain, ppg, pager['offset'], self._get_search_order(post)
		products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))
		print '----------pager-000000000@########', pager, products
		ProductAttribute = request.env['product.attribute']
		if products:
			# get all products without limit
			selected_products = Product.search(domain, limit=False)
			attributes = ProductAttribute.search([('attribute_line_ids.product_tmpl_id', 'in', selected_products.ids)])
		else:
			attributes = ProductAttribute.browse(attributes_ids)

		from_currency = request.env.user.company_id.currency_id
		to_currency = pricelist.currency_id
		compute_currency = lambda price: from_currency.compute(price, to_currency)
		order = request.website.sale_get_order()
		if order:
			from_currency = order.company_id.currency_id
			to_currency = order.pricelist_id.currency_id
			compute_currency = lambda price: from_currency.compute(price, to_currency)
		else:
			compute_currency = lambda price: price
		latest_product = request.env['latest.product'].sudo().search([])
		view_type = 'grid'
		if post.get('view_type') and post.get('view_type') == 'grid':
			view_type = 'grid'
		
		if post.get('view_type') and post.get('view_type') == 'list':
			view_type = 'list'
		
		values = {
			'website_sale_order': order,
			'compute_currency': compute_currency,
			'suggested_products': [],
			'search': search,
			'category': category,
			'attrib_values': attrib_values,
			'attrib_set': attrib_set,
			'pager': pager,
			'pricelist': pricelist,
			'products': products,
			'search_count': product_count,  # common for all searchbox
			'bins': Accessories().process(products, ppg),
			'rows': PPR,
			'categories': categs,
			'attributes': attributes,
			'compute_currency': compute_currency,
			'keep': keep,
			'latest_products': latest_product,
			'get_attribute_value_ids': self.get_attribute_value_ids,
			'view_type': view_type 
		}
		print '-order------', order, values
		if order:
			_order = order
			values['suggested_products'] = _order._cart_accessories()
			print"::::::::::::::::::Suggested:::::::::::::::::::::", values['suggested_products']
		print":::::::::::::::::Values::::::::::::::::::::::::::::::", values
			
		return request.render('custom_theme.suggested_products_list_custom', values)

	@http.route(['/shop_access/cart_access/update_access'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
	def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
		print '----call --cart --update----', product_id
		website_sale_custom().cart_update(product_id=product_id)
		return request.redirect("/accessories")

	def _filter_attributes(self, **kw):
		return {k: v for k, v in kw.items() if "attribute" in k}
