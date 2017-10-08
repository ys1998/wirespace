$(document).ready( function(){
	// function to update directory structure when a DIRECTORY is clicked
	$(document).on('click','.dir',function(){
		var item=$(this).attr("value");
		var curr_path=$('#back_button').attr("value");
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		var new_path=(curr_path=="")?item:curr_path+"/"+item;
		$.post( "",
			{'csrfmiddlewaretoken': csrf, 
			'name': new_path,
			'action':'open'},
			function( data, status ) {
				$( "#list" ).html( $(data).filter("#list").html());
			});
	});
	// IN-BROWSER VIEWING
	// function to display the clicked FILE in a new tab/window
	// creates a temporary form and posts it; removes the form later
	// this was a workaround from http://www.developerscoding.com/55/handle-file-download-from-ajax-post
	$(document).on('click','.file',function(){
		var item=$(this).attr("value");
		var curr_path=$('#back_button').attr("value");
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		var new_path=(curr_path=="")?item:curr_path+"/"+item;
		var form = $('<form class="hidden" method="POST" action="" target="_blank">');
        form.append($('<input type="hidden" name="name" value="' + new_path + '">'));
        form.append($('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'));
        form.append($('<input type="hidden" name="action" value="open">'));
        $('body').append(form);
        form.submit();
        $(".hidden").remove();
	});
	// function that handles moving to previous directory
	$(document).on('click','.back_button',function(){
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		var curr_path=$(this).attr("value");
		var prev_path=curr_path.substring(0,curr_path.lastIndexOf('/'));
		$.post( "", 
			{'csrfmiddlewaretoken': csrf, 
			'name': prev_path,
			'action':'open' }, 
			function( data, status ) {
				$( "#list" ).html( $(data).filter("#list").html() );
			});
	});
	// a general function to manage downloading of the clicked file/directory
	// creates a temporary form and posts it; removes the form later
	// this was a workaround from http://www.developerscoding.com/55/handle-file-download-from-ajax-post
	$(document).on('click','.download',function(){
		var item=$(this).attr("value");
		var curr_path=$('#back_button').attr("value");
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		var new_path=(curr_path=="")?item:curr_path+"/"+item;
		var form = $('<form class="hidden" method="POST" action="">');
        form.append($('<input type="hidden" name="name" value="' + new_path + '">'));
        form.append($('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'));
        form.append($('<input type="hidden" name="action" value="download">'));
        $('body').append(form);
        form.submit();
        $(".hidden").remove();
	});
});

