import odoo
from odoo import http
from odoo.http import request
from odoo.addons.website.models.website import slug


class QuickView(http.Controller):
    @http.route(['/productdata'], type='json', auth="public", website=True)    
    def fetchProduct(self,product_id=None, **kwargs):
        if product_id :
            product_record = request.env['product.template'].search([['id','=',product_id]])
            values={
                'product':product_record,
            }
            products = request.env['product.template'].search([['id','=',product_id]])                                                  
            response = http.Response(template="custom_theme.quick_view_fetch-record",qcontext=values)
        return response.render()
