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
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.web.controllers.main import ensure_db
from odoo.addons.website_sale.controllers.main import TableCompute
import werkzeug.utils
import werkzeug.wrappers

_logger = logging.getLogger(__name__)

PPG = 20  # Products Per Page
PPR = 4   # Products Per Row

class Website_custom(Website):

    def __init__(self):
        self.table = {}
    
    # ideally, this route should be `auth="user"` but that don't work in non-monodb mode.
    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            return werkzeug.utils.redirect('/', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        context = request.env['ir.http'].webclient_rendering_context()

        return request.render('web.webclient_bootstrap', qcontext=context)

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
        
    def _get_search_order(self, post):
        # OrderBy will be parsed in orm and so no direct sql injection
        # id is added to be sure that order is a unique sort key
        res = 'website_published desc , id desc'
        print '--order-----', post
        print '-res------------', res
        return res

    @http.route(['/'],
    type='http', auth="public", website=True)
    def index(self, page=0, category=None, search='', ppg=False, **post):
        # page = 'homepage'
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

        keep = QueryURL('/', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = ""
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
        print":::::::::::::::::::pager::::::::::::::::::::::::::", pager, product_count, domain, ppg, pager['offset'], self._get_search_order(post)
        products = Product.search(domain, offset=pager['offset'], order=self._get_search_order(post))[0:6]
        print '-------products000000---------', products, products
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
        latest_product = request.env['latest.product'].sudo().search([])
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products[0:6],
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'latest_products': latest_product,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            # 'rating_status': response.qcontext.get('rating_product'),
        }
        print"ggggggggggggggggggggggggggggggg", values['categories']
        if category:
            values['main_object'] = category
        res = request.render("custom_theme.custom_website_homepage", values)
    
        return res

    @http.route([
    '/category/<model("product.public.category"):category>',
    '/category/<model("product.public.category"):category>/page/<int:page>'],
    type='http', auth="public", website=True)
    def category(self, page=0, category=None, search='', ppg=False, **post):
        # page = 'homepage'
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

        keep = QueryURL('/', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = ""
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
        print":::::::::::::::::::pager::::::::::::::::::::::::::", pager, product_count, domain, ppg, pager['offset'], self._get_search_order(post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

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
        latest_product = request.env['latest.product'].sudo().search([])
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'latest_products': latest_product,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            # 'rating_status': response.qcontext.get('rating_product'),
        }
        print"ggggggggggggggggggggggggggggggg", values['categories'], category
        if category:
            values['main_object'] = category
        res = request.render("custom_theme.products_category_wise", values)
    
        return res
    
    @http.route([
    '/search',
    '/search/page/<int:page>'],
    type='http', auth="public", website=True)
    def search(self, page=0, category=None, search='', ppg=False, **post):
        # page = 'homepage'
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

        keep = QueryURL('/', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = ""
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
        print":::::::::::::::::::pager::::::::::::::::::::::::::", pager, product_count, domain, ppg, pager['offset'], self._get_search_order(post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'], order=self._get_search_order(post))

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
        latest_product = request.env['latest.product'].sudo().search([])
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg),
            'rows': PPR,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            'latest_products': latest_product,
            'get_attribute_value_ids': self.get_attribute_value_ids,
            # 'rating_status': response.qcontext.get('rating_product'),
        }
        print"ggggggggggggggggggggggggggggggg", values['categories'], category
        if category:
            values['main_object'] = category
        res = request.render("custom_theme.products_category_wise", values)
    
        return res

    @http.route('/product/featured', type='json', auth='public', website=True)
    def featured_product(self, ppg=False, **kw):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        Product = request.env['product.template']
        Products = Product.search([('is_featured', '=', True), ('website_published', '=', True)])
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])
        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        
        compute_currency = lambda price: from_currency.compute(price, to_currency)
        values = {'products': Products, 'bins': TableCompute().process(Products, ppg),'compute_currency': compute_currency, 'pricelist': pricelist,}
        print '=------values0000------', values
        a = request.env.ref('custom_theme.featured_product').render(values)
        print '-a----------', a
        return a

    @http.route('/product/specials', type='json', auth='public', website=True)
    def specials_product(self, ppg=False, **kw):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        Product = request.env['product.template']
        Products = Product.search([('is_special', '=', True), ('website_published', '=', True)])
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])
        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        compute_currency = lambda price: from_currency.compute(price, to_currency)
        
        values = {'products': Products, 'bins': TableCompute().process(Products, ppg), 'compute_currency': compute_currency, 'pricelist': pricelist,}
        print '=------values0000------', values
        a = request.env.ref('custom_theme.featured_product').render(values)
        print '-a----------', a
        return a
        #return request.render('custom_theme.featured_product', values)
    
    @http.route('/product/new', type='json', auth='public', website=True)
    def new_product(self, ppg=False, **post):
        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG
        Product = request.env['product.template']
        domain = request.website.sale_product_domain()
        Products = Product.search(domain, order=self._get_search_order(post))[0:6]
        print '--------prdcts------', Products, domain
        #Products = Product.search([('is_featured', '=', True), ('website_published', '=', True)])
        pricelist_context = dict(request.env.context)
        if not pricelist_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            pricelist_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(pricelist_context['pricelist'])
        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id
        
        compute_currency = lambda price: from_currency.compute(price, to_currency)
        values = {'products': Products, 'bins': TableCompute().process(Products, ppg),'compute_currency': compute_currency, 'pricelist': pricelist,}
        print '=------values0000------', values
        a = request.env.ref('custom_theme.featured_product').render(values)
        print '-a----------', a
        return a

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
        print new_values
        return new_values, errors, error_msg

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

        data = {}
        print '>>>>>>>', new_values
        if all_values.get('password'):
            data['password'] = all_values['password']
            print"fffffffffffffffffffffffffff", data['password']
            data['login'] = all_values['login']
            print"fffffffffffffff1111111111ffffffffffff", data['login']
            data['name'] = all_values['name']
            print"2222222222", data['name']
            print '-----User Creation---', data
            user_id = User.sudo().create(data)
            print user_id
            partner_id = user_id.partner_id
            user_id = user_id.id
            print partner_id
            partner_id = partner_id.id
            Partner.browse(partner_id).sudo().write(new_values)
                
        else:
            #create only authorized field and 'email ' instead of 'login'
            partner_id = Partner.sudo().create(new_values).id
            user_id = None
            print partner_id, user_id
        return partner_id, user_id

    @http.route('/register_custom', type='http', methods=['GET', 'POST'], auth="public", website=True)
    def redirect_register(self, **kw):
        order = request.website.sale_get_order()
        print order.partner_id.name, request.website.user_id.sudo().partner_id.name
        Partner = request.env['res.partner'].with_context(show_address=1).sudo()

        '''redirection = self.checkout_redirection(order)
        if redirection:
            return redirection'''

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
            #mode = ('new', 'billing')
            country_code = request.session['geoip'].get('country_code')
            
            if country_code:
                def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
            else:
                def_country_id = request.website.user_id.sudo().country_id 
        else:
            partner_id = order.partner_id.id
            #mode = ('edit', 'billing')
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
                '''if mode[1] == 'billing':
                    order.partner_id = partner_id
                    order.partner_shipping_id = partner_id
                    order.onchange_partner_id()'''
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

                print order.amount_total

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
                    res = request.redirect('/web/login?redirect=/')
                    print"ggggggggggggggggggggggggggg", res
                    return res
                    

                   
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
        return request.render("custom_theme.register_custom", render_values)

    @http.route('/web/session/logout', type='http', auth="none")
    def logout(self, redirect='/web'):
        request.session.logout(keep_db=True)
        print '--------------logout------------'
        return werkzeug.utils.redirect(redirect, 303)

    @http.route('/terms_conditions', type='http', auth="public", website=True)
    def terms_and_conditions(self, **kw):
        return request.render("custom_theme.custom_terms_condition")

    @http.route('/privacy_policy', type='http', auth="public", website=True)
    def privacy_and_policy(self, **kw):
        return request.render("custom_theme.custom_privacy_and_policy")
