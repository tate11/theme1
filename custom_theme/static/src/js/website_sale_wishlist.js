odoo.define('website_sale_wishlist.wishlist', function (require) {
"use strict";

var ajax = require('web.ajax');
var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');
var base = require('web_editor.base');
var website_sale_utils = require('web.utils');
var session = require('web.session');

if(!$('.oe_website_sale').length) {
    return $.Deferred().reject("DOM doesn't contain '.oe_website_sale'");
}



var ProductWishlist = Widget.extend({
    events: {
        'click #my_wish': 'display_wishlist',
    },
    init: function(){
        var self = this;
        this.wishlist_product_ids = [];
        // if (!odoo.session_info.is_website_user) {
        //     $.get('/shop/wishlist', {'count': 1}).then(function(res) {
        //         self.wishlist_product_ids = JSON.parse(res);
        //         self.update_wishlist_view();
        //     });
        // }
	console.log('----------INIT_---------')
	jQuery(document).on('click', '.o_add_wishlist', function(e) {
		var data = $(this)
		var prod_id = $(this).data('product-product-id');
		console.log('BUTON_____---------CLICLC_--', $(this), e.target, $(this).find('i').hasClass('fa fa-heart'), $(this).find('i').hasClass('fa fa-heart-o'))
		//debugger;
		if ($(this).find('i').hasClass('fa fa-heart-o')){
			console.log('ADDDDDDDDD', e.target)
			ajax.jsonRpc("/wishlist/user", 'call', {
		    }).then(function (result){
				console.log('-result-----', result, e)
				if(result){
		    		self.add_new_products(data, e);
					console.log('QQQQQQQQQQQQQQQQQQQ', prod_id)
					var products = $($.find('a[data-product-product-id='+prod_id+']>i'))
						
					products.removeClass('fa-heart-o').addClass('fa-heart')
					console.log('!!!!!!!!!!', products)
					return;
				}
				else{
					//$("#web.login").dialog();
					window.location.href = '/web/login'
				}
			});
		}
		if ($(this).find('i').hasClass('fa fa-heart')){
			var prod_id = $(this).data('product-product-id');
			//debugger;
			new Model('product.wishlist').call('search_read', [[]], {'fields': ['product_id', 'user_id']}).then(function(datas) {
				console.log('--------$$$$$^%888888888888', datas, datas.length, self.wishlist_product_ids)
				//debugger;
		        for (var i = 0; i < datas.length; i++) {
		            var prod_temp_id = datas[i]['product_id'][0];
					var usr_id = datas[i]['user_id'][0];
					console.log('--user----id---', usr_id, prod_temp_id, prod_id)
		            if (prod_temp_id == prod_id) {
		                var del_id = datas[i]['id'];
						console.log('-del-----id---', del_id)
		                new Model('product.wishlist').call('unlink', [[del_id]]);
						self.wishlist_product_ids.pop(del_id)
						//$(e.target).removeClass('fa-heart').addClass('fa-heart-o');
						console.log('QQQQQQQQQQQQQQQQQQQ', prod_id)
						var products = $($.find('a[data-product-product-id='+prod_id+']>i'))
						products.removeClass('fa-heart').addClass('fa-heart-o');
						console.log('!!!!!!!!!!', products)	
						//$('a.o_add_wishlist').attr('data-action','o_wishlist');
						return;
		            }
		        }
		    });
		}
	    return;	
	});
	
        $('.oe_website_sale .oe_website_sale .o_add_wishlist_dyn').click(function (e){
            //alert('adddddddddd', this);
	    console.log('ADDDDDDDDD', e.target)
	    $(e.target).removeClass('fa-heart-o').addClass('fa-heart')
            self.add_new_products($(this), e);
        });
		//consolr.log('')
        if ($('.wishlist-section').length) {
			
            $('.wishlist-section a.o_wish_rm').on('click', function (e){ self.wishlist_rm(e); });
            $('.wishlist-section a.o_wish_add').on('click', function (e){ self.wishlist_add(e); });
            // $('.wishlist-section a.o_wish_mv').on('click', function (e){ self.wishlist_mv(e); });
        }
    },
    add_new_products:function($el, e){
        var self = this;
		console.log('--------')
        console.log('------', !_.contains(self.wishlist_product_ids, product_id));
        var product_id = $el.data('product-product-id');
        console.log(product_id);


        if (odoo.session_info.is_website_user){
            console.log('yessss');
            this.warning_not_logged();
        } else {
				console.log('!!!!!!!!^^^^^^________')
                return ajax.jsonRpc('/shop/wishlist/add', 'call', {
                    'product_id': product_id
                }).then(function () {
                    self.wishlist_product_ids.push(product_id);
                    console.log('----&^^^^^^&&&&&&&&&&&&&&&&&&', self.wishlist_product_ids);
                    // $.each(self.wishlist_product_ids, function(val){
                    //     console.log('btn_' + val);
                    // $(.'btn_' + product_id).hide()		;
                    // });
                    //window.location.reload();
                    self.update_wishlist_view();
                    // website_sale_utils.animate_clone($('#my_wish'), $el.closest('form'), 10, 10);
                });
            
            // else{
            //     $('.btn_icon')
            // }
        }
    },
    display_wishlist: function() {
		console.log('----display-wishlist---------', this.wishlist_product_ids)
        if (odoo.session_info.is_website_user) {
            console.log('----odooo user----');
            this.warning_not_logged();
        }
        else if (this.wishlist_product_ids.length = 0) {
            alert('nnoooooo wishlist');
            this.update_wishlist_view();
            this.redirect_no_wish();
        }
        else {           
            window.location = '/shop/wishlist';
            // _.each(this.wishlist_product_ids, function(val){
            //     $(.'btn_' + product_id).hide();
            // });
        }
    },
    update_wishlist_view: function() {
		console.log('--update----wiashlist00000000', this.wishlist_product_ids)
        if (this.wishlist_product_ids.length > 0) {
            $('#my_wish').show();
            $('.my_wish_quantity').text(this.wishlist_product_ids.length);
        }
        else {
            $('#my_wish').show();
        }
    },
    wishlist_rm: function(e){
		console.log('***************************', this.wishlist_product_ids)
        var tr = $(e.currentTarget).parents('tr');
        var wish = tr.data('wish-id');
        var product = tr.data('product-id');
        new Model('product.wishlist')
            .call('write', [[wish], { active: false }, base.get_context()])
            .then(function(){
                $(tr).remove();
            });
        this.wishlist_product_ids = _.without(this.wishlist_product_ids, product);
        if ($('.table-responsive tbody tr').length <= 1) {
			this.update_wishlist_view();
            this.redirect_no_wish();
        }
        this.update_wishlist_view();
    },
    wishlist_add: function(e){
	console.log('wishlist0-add-----------')
        var tr = $(e.currentTarget).parents('tr');
        var product = tr.data('product-id');

        // can be hidden if empty
        // $('#my_cart').removeClass('hidden');
        // website_sale_utils.animate_clone($('#my_cart'), tr, 0, 0);
        this.add_to_cart(product, tr.find('qty').val() || 1);
    },
    // wishlist_mv: function(e){
    //     var tr = $(e.currentTarget).parents('tr');
    //     var product = tr.data('product-id');

    //     // $('#my_cart').removeClass('hidden');
    //     // website_sale_utils.animate_clone($('#my_cart'), tr, 0, 0);
    //     this.add_to_cart(product, tr.find('qty').val() || 1);
    //     var wish = tr.data('wish-id');

    //     new Model('product.wishlist')
    //         .call('write', [[wish], { active: false }, base.get_context()])
    //         .then(function(){
    //             $(tr).hide();
    //         });
    //     console.log(product);
    //     this.wishlist_product_ids = _.without(this.wishlist_product_ids, product);
    //     console.log(this.wishlist_product_ids);
    //     if (this.wishlist_product_ids.length == 0) {

    //         window.location = '/shop/cart';
            
    //     }
        
    //     this.update_wishlist_view();

    //     // this.wishlist_rm(e);
    // },

    add_to_cart: function(product_id, qty_id) {
	console.log('----ADD-TO0--CART-----')
        ajax.jsonRpc("/shop/cart/update_json", 'call', {
            'product_id': parseInt(product_id, 10),
            'add_qty': parseInt(qty_id, 10)
        }).then(function (data) {

	    console.log('CATY_-------', data)
            var $q = $(".my_cart_quantity");

            console.log(data.quantity);
            if (data.cart_quantity) {
                    $q.parents('li:first').removeClass("hidden");
                }
                else {
                    $q.parents('li:first').addClass("hidden");
                    $('a[href^="/shop/checkout"]').addClass("hidden");
                }
		console.log('AAAAAAAAAAAAAAAAAAAAA')
                $q.html(data.cart_quantity).hide().fadeIn(600);
                $q.val(data.quantity);

        });
    },
    redirect_no_wish: function() {
        window.location.replace('/');
		//location.reload();
    },
    warning_not_logged: function() {
        window.location = '/shop/wishlist';
    }
});

new ProductWishlist();

$('.partner_remove').on('click', function(e){
            var self = this;
            e.preventDefault();
            var tr = $(e.currentTarget).parents('tr');
            var ship_id = parseInt($(this).siblings('input').val());
            console.log(ship_id);
            var d = new Model("res.partner").call("search_read", [[["id", "=", ship_id]]]).then(function(result){
                var da = $(this).closest('tr').find(d).val(0).trigger('change');
                tr.remove();
            })
            var d = new Model("res.partner").call("unlink", [ship_id]).then(function(result){
                
            })
        });

 $('.oe_cart').on('click', '.js_edit_address', function() {
            alert('---');
            $(this).parent('div.one_kanban').find('form.hide').attr('action', '/edit_address').submit();
        });


});
