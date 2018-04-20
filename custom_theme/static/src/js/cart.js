odoo.define('custom_theme.website_sale', function (require) {
    "use strict";

    var base = require('web_editor.base');
    var ajax = require('web.ajax');
    var utils = require('web.utils');
    var core = require('web.core');
    var config = require('web.config');
    var _t = core._t;
    console.log("============6666666666666===================", _t)

    $('.a-submit-data, #comment .a-submit-data').off('click').on('click', function (event) {
        if (!event.isDefaultPrevented() && !$(this).is(".disabled")) {
        	/*event.preventDefault();
		    console.log("------------66666--------", event)
		    var $link = $(event.currentTarget);
		    console.log("==========0000000=============", $link)
		    var $input = $link.parent().find("input");
		    console.log("ggggggggggggggggggggggggggg", $input)
		    var product_id = +$input.closest('*:has(input[name="product_id"])').find('input[name="product_id"]').val();
		    console.log("gggggg5555555555555555555555555", product_id)*/
            $(this).closest('form').submit();
            console.log("==========4444444=====111111===============", $(this).closest('form'))
        }
        if ($(this).hasClass('a-submit-disable')){
            $(this).addClass("disabled");
        }
        if ($(this).hasClass('a-submit-loading')){
            var loading = '<span class="fa fa-cog fa-spin"/>';
            console.log("===========loading===============", loading)
            var fa_span = $(this).find('span[class*="fa"]');
            console.log("============000000000000===============", fa_span)
            if (fa_span.length){
                fa_span.replaceWith(loading);
            }
            else{
                $(this).append(loading);
            }
        }
    });
   
});
