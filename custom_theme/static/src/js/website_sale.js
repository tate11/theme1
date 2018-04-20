odoo.define('custom_theme.website_sale_custom', function (require) {
    "use strict";

    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var _t = core._t;
    console.log("fffffffffffffffffffffffffffff", _t)

	 if(!$('.oe_website_sale').length) {
        return $.Deferred().reject("DOM doesn't contain '.oe_website_sale'");
    }

	$('.oe_website_sale').each(function () {
        var oe_website_sale = this;
		console.log('!!!!!!!!!!', oe_website_sale)
		var clickwatch = (function(){
              var timer = 0;
              return function(callback, ms){
                clearTimeout(timer);
                timer = setTimeout(callback, ms);
              };
        })();
		$(oe_website_sale).on("change", ".oe_cart input.js_quantity[data-product-id]", function () {
          var $input = $(this);
			if ($input.data('update_change')) {
		            return;
		   	}
		    var value = parseInt($input.val() || 0, 10);
			if (isNaN(value)) {
				value = 1;
			}
		      var $dom = $(this).closest('tr');
		      //var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
		      var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
		      var line_id = parseInt($input.data('line-id'),10);
		      var product_ids = [parseInt($input.data('product-id'),10)];
		      clickwatch(function(){
		        $dom_optional.each(function(){
		            $(this).find('.js_quantity').text(value);
		            product_ids.push($(this).find('span[data-product-id]').data('product-id'));
		        });
		        $input.data('update_change', true);

		        ajax.jsonRpc("/shop/cart/update_json", 'call', {
		            'line_id': line_id,
		            'product_id': parseInt($input.data('product-id'), 10),
		            'set_qty': value
		        }).then(function (data) {
		            $input.data('update_change', false);
					console.log('AAAAAAAAAAAAAAAAAAAAAAA', data, $input)
		            var check_value = parseInt($input.val() || 0, 10);
		            if (isNaN(check_value)) {
		                check_value = 1;
		            }
		            if (value !== check_value) {
		                $input.trigger('change');
		                return;
		            }
		            var $q = $(".my_cart_quantity");
		            if (data.cart_quantity) {
		                $q.parents('li:first').removeClass("hidden");
		            }
		            else {
					console.log('------------else---custom-------')
		                $q.parents('li:first').removeClass("hidden");
						window.location.reload();
		                $('a[href^="/shop/checkout"]').addClass("hidden");
		            }
					console.log('-html------------', $q.text(data.cart_quantity))
		            $q.text(data.cart_quantity);
		            $input.val(data.quantity);
		            $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).html(data.quantity);

		            $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();

		            if (data.warning) {
		                var cart_alert = $('.oe_cart').parent().find('#data_warning');
		                if (cart_alert.length === 0) {
		                    $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">'+
		                            '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
		                }
		                else {
		                    cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
		                }
		                $input.val(data.quantity);
		            }
		        });
		      }, 500);
		});
	});
	$('.p_list_view').on('click', function(e){
		console.log('-grid0---------click----------', $(this));
		//debugger;
		$(this).addClass('active');
		$('.p_grid_view').removeClass('active')
		$('.view_type').val('list')
		console.log('-0-----GRID-----', $('.view_type'))
		$('.oe_list').removeClass('hidden');
		$('.Product_layout1').addClass('hidden');
		
	});
	$('.p_grid_view').on('click', function(e){
		console.log('-grid0---------click----------');
		$(this).addClass('active');
		$('.p_list_view').removeClass('active')
		$('.view_type').val('grid')
		$('.Product_layout1').removeClass('hidden');
		$('.oe_list').addClass('hidden');
		
	});
	/*jQuery('.search_icon').on("click", function(){
	   
		if ( $('#search').css('display') == 'none' ) {
			$(this).addClass("active");
			$('#search').css({'display':'block'}).animate({width:402, opacity:1},300);
			if ($(".box-cart .toggle-wrap").find('.toggle').hasClass('active')) { 
				$(".box-cart .toggle-wrap").find('.active').toggleClass('active').parent().find('.toggle_cont').slideToggle();			
			}
			if ($(".nav.toggle-wrap").find('.toggle').hasClass('active')) { 
				$(".nav.toggle-wrap").find('.active').toggleClass('active').parent().find('.toggle_cont').slideToggle();			
			}
		} else {
			$(this).parent().find('.active').removeClass('active');
			$('#search').animate({width:0, opacity:0},{duration:300, done:function(){$(this).css({'display':'none'});}});
		}
		
   });*/
	$('.search_icon').on('click', function(e){
		console.log('-search---------click----------', $(this), $('.search_formds'));
		$('.search_formds').removeClass('hidden');
		$('.search_formds').addClass('change-size'),function(){
				console.log('test....................');
				$('.search_formds').removeClass('change-size');
		};
		$(this).addClass('hidden');
		//$('.search_formds').fadeIn(3000);
		$('.search_icon_close').removeClass('hidden');
		
		//debugger;
		//$('.search_formds').addClass('open');
		//$('.search_icon').prop('aria-expanded', true);
		//$('.search_formds').removeClass('hidden');
		
	});
	$('.search_icon_close').on('click', function(e){
		console.log('-search---------click----------', $(this), $('.search_formds'));
		$('.search_formds').addClass('hidden');
		
		$('.search_icon').removeClass('hidden');
		$(this).addClass('hidden');
		//$('.search_icon_close').removeClass('hidden');
		
		//debugger;
		//$('.search_formds').addClass('open');
		//$('.search_icon').prop('aria-expanded', true);
		//$('.search_formds').removeClass('hidden');
		
	});
	$('.featured').on('click', function(e){
		ajax.jsonRpc("/product/featured", 'call', {
		}).then(function (result){
			console.log('-----result------', result)
			console.log('--------##########---', $('div .fillers_tabs_inner'))
			//debugger;
			$('div .fillers_tabs_inner').html(result)
			$('.products_pager').html('')
			//$('span .products').add(result)
		});
	});
	$('.specials').on('click', function(e){
		ajax.jsonRpc("/product/specials", 'call', {
		}).then(function (result){
			console.log('-----result------', result)
			console.log('--------##########---', $('div .fillers_tabs_inner'))
			//debugger;
			$('div .fillers_tabs_inner').html(result)
			$('.products_pager').html('')
			//$('span .products').add(result)
		});
	});

	$('.new').on('click', function(e){
		ajax.jsonRpc("/product/new", 'call', {
		}).then(function (result){
			console.log('-----result------', result)
			console.log('--------##########---', $('div .fillers_tabs_inner'))
			//debugger;
			$('div .fillers_tabs_inner').html(result)
			$('.products_pager').html('')
			//$('span .products').add(result)
		});
	});
	
});
