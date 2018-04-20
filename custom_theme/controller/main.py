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
from odoo.addons.website.controllers.main import Home
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.web.controllers.main import set_cookie_and_redirect


# from addons.web.controllers.main import Session
import werkzeug.utils
import werkzeug.wrappers

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row


class website_sale_custom(WebsiteSale):
	
#home
	@http.route([
		'/shop',
		'/shop/page/<int:page>',
		'/shop/category/<model("product.public.category"):category>',
		'/shop/category/<model("product.public.category"):category>/page/<int:page>'
	], type='http', auth="public", website=True)
	def shop(self, page=0, category=None, search='', ppg=False, **post):
		print"=================sssssssss============================="

		# response = super(website_sale_custom, self).shop(page=page, category=category, search=search, ppg=ppg, **post)
		# print '>>>>>>>>>>', response
		# response.qcontext.update({
		# 	'get_attribute_value_ids': self.get_attribute_value_ids,
		# 	'rating_status': response.qcontext.get('rating_product'),
		# })
		# print response

				
		return request.redirect("/")

#Cart

	@http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
	def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
		request.website.sale_get_order(force_create=1)._cart_update(
			product_id=int(product_id),
			add_qty=add_qty,
			set_qty=set_qty,
			attributes=self._filter_attributes(**kw),
		)
		return request.redirect("/")

	@http.route(['/shop/cart_custom/update_custom'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
	def cart_update_data(self, product_id, add_qty=1, set_qty=0, **kw):
		request.website.sale_get_order(force_create=1)._cart_update(
			product_id=int(product_id),
			add_qty=add_qty,
			set_qty=set_qty,
			attributes=self._filter_attributes(**kw),
		)
		return request.redirect("/shop/cart")

	@http.route(['/shop/cart_custom_data/update_custom_data'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
	def cart_update_data_custom(self, product_id, add_qty=1, set_qty=0, **kw):
		request.website.sale_get_order(force_create=1)._cart_update(
			product_id=int(product_id),
			add_qty=add_qty,
			set_qty=set_qty,
			attributes=self._filter_attributes(**kw),
		)
		return request.redirect("/shop/cart")

	def _filter_attributes(self, **kw):
		return {k: v for k, v in kw.items() if "attribute" in k}

# Checkout

	@http.route(['/shop/checkout'], type='http', methods=['GET', 'POST'], auth="public", website=True)
	def checkout(self, **kw):
		order = request.website.sale_get_order()
		print order.partner_id.name, request.website.user_id.sudo().partner_id.name
		Partner = request.env['res.partner'].with_context(show_address=1).sudo()

		redirection = self.checkout_redirection(order)
		if redirection:
			return redirection

		print order.partner_id.name, order.partner_id.company_id, order.partner_id.city, order.partner_id.country_id
		print order.partner_id.id
		mode = (False, False)
		def_country_id = order.partner_id.country_id
		values, errors, payment_values = {}, {}, {}
		acquirers = []
		tokens = {}
		
		partner_id = int(kw.get('partner_id', -1))

		if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
			partner_id = -1
			print '------------------', partner_id
			mode = ('new', 'billing')
			country_code = request.session['geoip'].get('country_code')
			
			if country_code:
				def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
			else:
				def_country_id = request.website.user_id.sudo().country_id 
		else:
			partner_id = order.partner_id.id
			mode = ('edit', 'billing')
			if mode:
				user_id = request.env['res.users'].sudo().search([('partner_id', '=', partner_id)])
				print user_id
				values = Partner.browse(partner_id)
				print '------values on partner----', values

		#Payment
		
		#when posted
		if 'submitted' in kw:
			print 'hellllllllllloooooooooooo'
			pre_values = self.values_preprocess(order, mode, kw)
			print '---------pre_values--------', pre_values
			errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
			post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)
			print '--------post-----', post, errors, error_msg
			if errors:
				errors['error_message'] = error_msg
				values = kw
			else:
				partner_id, user_id = self._checkout_form_save_checkout(mode, post, kw)

				print '----ACTUAL PARTNER and USER ID-------', partner_id, user_id
				if mode[1] == 'billing':
					order.partner_id = partner_id
					order.partner_shipping_id = partner_id
					order.onchange_partner_id()
				order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
				
				

				request.session['sale_last_order_id'] = order.id
				request.website.sale_get_order(update_pricelist=True)
				
				#PAYMENT DETAIL

				SaleOrder = request.env['sale.order']
				shipping_partner_id = False
				if order:
					if order.partner_shipping_id.id:
						shipping_partner_id = order.partner_shipping_id.id
					else:
						shipping_partner_id = order.partner_invoice_id.id

				payment_values = {
					'website_sale_order': order
				}

				payment_values['errors'] = SaleOrder._get_errors(order)
				payment_values.update(SaleOrder._get_website_data(order))
				if not payment_values['errors']:
					acquirers = request.env['payment.acquirer'].search(
						[('website_published', '=', True), ('company_id', '=', order.company_id.id)]
					)
					payment_values['acquirers'] = []
					for acquirer in acquirers:
						acquirer_button = acquirer.with_context(submit_class='btn btn-primary', submit_txt=_('Pay Now')).sudo().render(
							'/',
							order.amount_total,
							order.pricelist_id.currency_id.id,
							values={
								'return_url': '/shop/payment/validate',
								'partner_id': shipping_partner_id,
								'billing_partner_id': order.partner_invoice_id.id,
							}
						)
						acquirer.button = acquirer_button
						payment_values['acquirers'].append(acquirer)

					payment_values['tokens'] = request.env['payment.token'].search([('partner_id', '=', order.partner_id.id), ('acquirer_id', 'in', acquirers.ids)])
					print '------------', payment_values

				if user_id:
					print '))))))))))))))))', user_id
					request.redirect('/web/login?redirect=/shop/checkout/')
					

				   
		order = request.website.sale_get_order(force_create=1)
		country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
		country = country and country.exists() or def_country_id
		render_values = {
			'order': order,
			'partner_id': partner_id,
			'mode': mode,
			'checkout': values,
			'country': country,
			'countries': country.get_website_sale_countries(mode=mode[1]),
			"states": country.get_website_sale_states(mode=mode[1]),
			'error': errors,
			'payment_values': payment_values,
			# 'acquirers': payment_values['acquirers'] or acquirers,
			# 'tokens': payment_values['tokens'] or tokens,
			
		}
		
		print '-------------------render values--------', render_values
		return request.render("website_sale.checkout", render_values)

	def checkout_form_validate(self, mode, all_form_values, data):
		error = dict()
		error_message = []

		# Required fields from form
		required_fields = filter(None, (all_form_values.get('field_required') or '').split(','))
		# required_fields += mode[1] == 'shipping' and self._get_mandatory_shipping_fields() or self._get_mandatory_billing_fields()

		if data.get('country_id'):
			country = request.env['res.country'].browse(int(data.get('country_id')))
			if 'state_code' in country.get_address_fields() and country.state_ids:
				required_fields += ['state_id']

		# error message for empty required fields
		for field_name in required_fields:
			if not data.get(field_name):
				error[field_name] = 'missing'

		# email validation
		if data.get('login') and not tools.single_email_re.match(data.get('login')):
			error["login"] = 'error'
			error_message.append(_('Invalid Email! Please enter a valid email address.'))

		# vat validation
		Partner = request.env['res.partner']
		if data.get("vat") and hasattr(Partner, "check_vat"):
			if data.get("country_id"):
				data["vat"] = Partner.fix_eu_vat_number(data.get("country_id"), data.get("vat"))
			check_func = request.website.company_id.vat_check_vies and Partner.vies_vat_check or Partner.simple_vat_check
			vat_country, vat_number = Partner._split_vat(data.get("vat"))
			if not check_func(vat_country, vat_number):
				error["vat"] = 'error'

		if [err for err in error.values() if err == 'missing']:
			error_message.append(_('Some required fields are empty.'))

		return error, error_message

	def _checkout_form_save_checkout(self, mode, checkout, all_values):
		Partner = request.env['res.partner']
		User = request.env['res.users']
		new_values = {}
		authorized_fields = request.env['ir.model'].sudo().search([('model', '=', 'res.partner')])._get_form_writable_fields()
		for k, v in checkout.items():
			if k in authorized_fields and v is not None:
				new_values[k] = v
		if checkout.get('street2'):
			new_values['street2'] = checkout['street2']
		if checkout.get('fax'):
			new_values['fax'] = checkout['fax']
		
		print '---create and write on partner----', new_values
		print '-------error--------'
		print mode
		if mode[0] == 'new':
			print '>>>>>>>'
			if all_values.get('password'):
				
				vals = {
				'login' :  checkout['email'],
				'password' : checkout['password'],
				'name': checkout['name'],

				}
				print '-----User Creation---', vals
				user_id = User.sudo().create(vals)
				print "dddddddddddddddddddd", user_id
				partner_id = user_id.partner_id
				user_id = user_id.id
				print "aaaaaaaaaaaaaaaaaa", partner_id
				partner_id = partner_id.id
				Partner.browse(partner_id).sudo().write(new_values)
				
			else:
				#create only authorized field and 'email ' instead of 'login'
				partner_id = Partner.sudo().create(new_values).id
				user_id = None
			return partner_id, user_id


		elif mode[0] == 'edit':
			print '<<<<<<<<<<<<'
			partner_id = int(all_values.get('partner_id', 0))
			if partner_id:
				# double check
				order = request.website.sale_get_order()
				shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
				if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
					return Forbidden()
				#authorized field should be write
				Partner.browse(partner_id).sudo().write(new_values)
				user_id = User.sudo().search([('partner_id', '=', partner_id )], limit=1)
				return partner_id, user_id.id   

	def values_preprocess(self, order, mode, values):
		return values

	def values_postprocess(self, order, mode, values, errors, error_msg):
		new_values = {}
		authorized_fields = request.env['ir.model'].sudo().search([('model', '=', 'res.partner')])._get_form_writable_fields()
		for k, v in values.items():
			# don't drop empty value, it could be a field to reset
			if k in authorized_fields and v is not None:
				new_values[k] = v
			else:  # DEBUG ONLY
				if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
					_logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)
		
		if values.get('login'):
			new_values['email'] = values['login']
		if values.get('fax'):
			new_values['fax'] = values['fax']
		if values.get('street2'):
			new_values['street2'] = values['street2']
		if mode[0] == 'new':
			if values.get('password'):
				new_values['password'] = values['password']     
			
			new_values['customer'] = True
			new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id

			lang = request.lang if request.lang in request.website.mapped('language_ids.code') else None
			if lang:
				new_values['lang'] = lang
		if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
			new_values['type'] = 'other'


		if mode[1] == 'shipping':
			print 'ffffffffffffffffffffff', mode
			#new_values['parent_id'] = order.partner_id.commercial_partner_id.id
			new_values['type'] = 'delivery'
		return new_values, errors, error_msg


	def checkout_redirection(self, order):
		# must have a draft sale order with lines at this point, otherwise reset
		if not order or order.state != 'draft':
			request.session['sale_order_id'] = None
			request.session['sale_transaction_id'] = None
			return request.redirect('/')

		# if transaction pending / done: redirect to confirmation
		tx = request.env.context.get('website_sale_transaction')
		if tx and tx.state != 'draft':
			return request.redirect('/shop/payment/confirmation/%s' % order.id)


# Wish List
	@http.route(['/shop/wishlist/add'], type='json', auth="user", website=True)
	def add_to_wishlist(self, product_id, price=False, **kw):
		if not price:
			
			pricelist_context = dict(request.env.context)
			if not pricelist_context.get('pricelist'):
				pricelist = request.website.get_current_pricelist()
				pricelist_context['pricelist'] = pricelist.id
			else:
				pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

			from_currency = request.env.user.company_id.currency_id
			to_currency = pricelist.currency_id
			compute_currency = lambda price: from_currency.compute(price, to_currency)

			# pricelist_context, pl = self._get_compute_currency_and_context()
			p = request.env['product.product'].with_context(pricelist_context, display_default_code=False).browse(product_id)
			price = p.website_price

		request.env['product.wishlist']._add_to_wishlist(
			request.env.user.partner_id.id,
			pricelist.id,
			pricelist.currency_id.id,
			request.website.id,
			price,
			product_id,
			request.uid
		)
		return True

	@http.route(['/shop/wishlist'], type='http', auth="public", website=True)
	def get_wishlist(self, count=False, **kw):
		print '---------AQQQQQQQQQQQQQQQQQQQQQQ', request.website.user_id
		values = request.env['product.wishlist'].with_context(display_default_code=False).sudo().search([('partner_id', '=', request.env.user.partner_id.id)])
		if count:
			return request.make_response(json.dumps(values.mapped('product_id').ids))

		# if not len(values):
		# 	return request.redirect(	"/shop")

		return request.render("custom_theme.product_wishlist", dict(wishes=values))


class CustomTheme(http.Controller):
	@http.route('/wishlist/user', type='json', auth="public", website=True)
	def check_login_user(self, **post):
		print '--------call-----jsonpp------', request.session
		if request.session.uid:
			return True
		else:
			print '-------else---------'
			return False

		
