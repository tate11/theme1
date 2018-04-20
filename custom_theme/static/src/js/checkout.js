odoo.define('custom_theme.checkout', function (require) {
    "use strict";

    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    var _t = core._t;
    
    $('#register_account').click(function() {
    	var value = $("form input[type='radio']:checked").val();
    	if(value == 'register'){
				alert('register');
				$('.password').show()				
			}
		else{
			alert('guest user');
			$('.password').hide()
			}
		$("#account-billing").prop("aria-expanded", true,);
		$("#account-billing").prop("style", false);
		$('#account-billing').addClass('in');
		$('#checkout-option').removeClass('in');
		$('#checkout-option').prop("aria-expanded", false);
		$('#checkout-option').prop("style", true);

		});

    // $('.submit_register').click(function(ev){

    //     alert('hhhhhhhhh');
    //     var $form = $(ev.currentTarget).parents('form');
    //     console.log($form)

    // 	ajax.jsonRpc("/shop/checkout/register", 'call', {
                
    //         }).then(function (result) {
    //             alert('fomr submit');
    //             $form.html(result);
    //             $form.submit();
    //         });


    // });


   


});