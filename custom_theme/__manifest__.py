# -*- coding: utf-8 -*-
{
    'name': "Custom Theme",

    'summary': """
        Website pages for Login, Register and forgot password """,

    'description': """
    """,

    'author': "MPTechnolabs",
    'website': "",
    'category': 'Website',
    'version': '0.1',
    'depends': ['web', 'website', 'sale', 'auth_signup', 'website_sale', 'product', 'payment_transfer', 'payment_paypal', 'odoo_branding', 'website_mass_mailing'],
    'data': [
    	'security/ir.model.access.csv',
	#'view/slider_data_view.xml',
	'view/product_view.xml',
    	'views/shop_product.xml',
    	'views/assets.xml',
    	'views/main_data.xml',
    	'views/login_signup.xml',
    	'views/register.xml',
    	'views/theme_template_wish_list.xml',
    	'views/forgot_password.xml',
    	'views/shop_cart.xml',
        'views/checkout.xml',
        'views/confirm_order.xml',
        'views/latest_product_view.xml',
        'views/wishlist.xml',
        'views/contact_us_view.xml',
        'views/accessories_views.xml',
        'views/my_account_view.xml',
        'views/account_information_view.xml',
        'views/address_book_view.xml',
        'views/edit_address.xml',
        'views/order_history.xml',
        'views/res_partner_view.xml',
        'views/terms_condition_view.xml',
        'views/privacy_policy_view.xml',
		'views/category_view.xml',
    ],
}
