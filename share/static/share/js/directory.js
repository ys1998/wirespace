$(document).ready( function(){
	$(document).on('click','.button',function(){
		var address=$(this).val();
		$("#list").load("/share/"+address);
	});
	$(document).on('click','.back_button',function(){
		var address = $(this).val();
		address=address.substring(0,address.lastIndexOf('/'));
		address=address.substring(0,address.lastIndexOf('/'));
		$("#list").load("/share/"+address);
	});
});

