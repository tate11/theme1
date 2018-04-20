odoo.define('quickview.gets_product', function(require) {	
	
	"use strict";	
	var base = require('web_editor.base');	
	var ajax = require('web.ajax');	
	var utils = require('web.utils');	
	var core = require('web.core');	
	var _t = core._t;
	
	
	 // add website_sale & wishlist , compare and rating script for quick view
	 function addScript()
	 { 
	    var script=document.createElement('script');
	    script.type='text/javascript';
	    console.log("------------0000000000--------------", script)
	    script.src="/custom_theme/static/src/js/function_add.js";
	    console.log("fffffffffff44444444444444444", script.src)  	    
	    $("head").append(script);
	  }
		
		function close_quickview()
		{                
			$('.mask').css("display","none");
			$('.mask_cover').css("display","none");
			$("script[src='/custom_theme/static/src/js/function_add.js']").remove()
			
		}
		function get_quickview(pid)
		{
				pid=pid;
				console.log("========ppppppp============", pid)
				ajax.jsonRpc('/productdata', 'call', {'product_id':pid}).then(function(data) {
					
				$(".mask_cover").append(data)
				$(".mask").fadeIn();
				$('.cus_theme_loader_layout').addClass('hidden');
				$(".mask_cover").css("display","block");
		    	addScript();
		    	console.log("ddddddddddddddddddddddd", addScript())
		    	$(".close_btn").click(function()
		    	{
		    		close_quickview()
		    		console.log("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh", close_quickview())
		    		$('.mask_cover').empty(data);
		    	});
		    	$(document).on( 'keydown', function(e)
		    	{
		    		if(e.keyCode === 27) 
		    		{
		    			if(data)
		    			{
		    				close_quickview()
		    				$('.mask_cover').empty(data);
		    			}
		    		}
		    	});
			});
		}
	$(".quick-view-a").click(function(){ 
			$('.cus_theme_loader_layout').removeClass('hidden');
			console.log("========qqqqqqq==========")
			var pid = $(this).attr('data-id');
			console.log("========888888========", pid)
			get_quickview(pid)
			console.log("ggggggggggggggggggggggggggggggggggggggggg")
			
	});
	
	return{
		get_quickview:get_quickview
	};
});
