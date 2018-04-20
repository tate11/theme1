from odoo import api, fields, models


class ProductWishlist(models.Model):
	_name = 'product.wishlist'

	partner_id = fields.Many2one('res.partner', string='Owner', required=True)
	pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help='Pricelist when added')
	currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id', readonly=True)
	website_id = fields.Many2one('website', required=True)
	price = fields.Monetary(digits=0, currency_field='currency_id', string='Price', help='Price of the product when it has been added in the wishlist')
	price_new = fields.Float(compute='compute_new_price', string='Current price', help='Current price of this product, using same pricelist, ...')
	product_id = fields.Many2one('product.product', string='Product', required=True)
	active = fields.Boolean(default=True, required=True)
	create_date = fields.Datetime('Added Date', readonly=True, required=True)
	user_id = fields.Many2one('res.users', string='User')
	product_temp_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
	@api.multi
	@api.depends('pricelist_id', 'currency_id', 'product_id')
	def compute_new_price(self):
		for wish in self:
			wish.price_new = wish.product_id.with_context(pricelist=wish.pricelist_id.id).website_price

	@api.model
	def _add_to_wishlist(self, partner_id, pricelist_id, currency_id, website_id, price, product_id, user_id):
		wish = self.env['product.wishlist'].sudo().create({
			'partner_id': partner_id,
			'pricelist_id': pricelist_id,
			'currency_id': currency_id,
			'website_id': website_id,
			'price': price,
			'product_id': product_id,
		'user_id': user_id
		})
		return wish


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	is_featured = fields.Boolean('Is Featured')
	is_special = fields.Boolean('Is Specials')

	@api.multi
	def is_wishlist(self):
		self.ensure_one()
		print '************', self.id
		if self.id:
			product_wishlisted = self.env['product.wishlist'].sudo().search(
				[('product_temp_id', '=', self.id),
				('user_id', '=', self.env.uid)])
			print '------prdct-wish;lisetd000---', product_wishlisted
			if len(product_wishlisted) > 0:
				return True
			else:
				return False

