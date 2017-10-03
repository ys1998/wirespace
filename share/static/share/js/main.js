$(document).ready( function(){
	// function to update directory structure when a DIRECTORY is clicked
	$(document).on('click','.dir',function(){
		var item=$(this).attr("value");
		var curr_path=$('#back_button').attr("value");
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		var new_path=(curr_path=="")?item:curr_path+"/"+item;
		// $.post( "",
		// 	{'csrfmiddlewaretoken': csrf, 
		// 	'name': new_path,
		// 	'action':'open'},
		// 	function( data, status ) {
		// 		$( "#list" ).html( $(data).filter("#list").html());
		// 	});
		$.post( "open/",
			{'csrfmiddlewaretoken': csrf, 
			'address': curr_path,
			'item':item},
			function( data, status ) {
				// DEAL WITH THE DATA HERE
				// I AM MODIFYING THE div WITH id="list" HERE
				$( "#list" ).empty();
				$("#list").append("<div id=\"back\"><button class=\"back_button\" id=\"back_button\" value=\""+data.address+"\">Back</button></div>");
				var content="<ul>";
				$.each(data.file, function(index,element){
					content+="<li><button class=\"file\" value=\""+element+"\">"+element+"</button><button class=\"download\" value=\""+element+"\">Download</button></li>";
				});
				$.each(data.dir, function(index,element){
					content+="<li><button class=\"dir\" value=\""+element+"\">"+element+"</button><button class=\"download\" value=\""+element+"\">Download</button></li>";
				});
				$.each(data.hidden, function(index,element){
					content+="<li><button class=\"dir\" value=\""+element+"\">"+element+"</button><button class=\"download\" value=\""+element+"\">Download</button></li>";
				});
				content+="</ul>";
				$("#list").append(content);
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
		// var new_path=(curr_path=="")?item:curr_path+"/"+item;
		// var form = $('<form class="hidden" method="POST" action="" target="_blank">');
  		// form.append($('<input type="hidden" name="name" value="' + new_path + '">'));
  		// form.append($('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'));
  		// form.append($('<input type="hidden" name="action" value="open">'));
  		// $('body').append(form);
  		var new_path=(curr_path=="")?item:curr_path+"/"+item;
		var form = $('<form class="hidden" method="POST" action="open/" target="_blank">');
        form.append($('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'));
        form.append($("<input type=\"hidden\" name=\"item\" value=\""+item+"\">"));
        form.append($("<input type=\"hidden\" name=\"address\" value=\""+curr_path+"\">"));
        $('body').append(form);

        form.submit();
        $(".hidden").remove();
	});
	// function that handles moving to previous directory
	$(document).on('click','.back_button',function(){
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		var curr_path=$(this).attr("value");
		var curr_path=curr_path.substring(0,curr_path.lastIndexOf('/'));
		var address=curr_path.substring(0,curr_path.lastIndexOf('/'));
		var item=curr_path.substring(curr_path.lastIndexOf('/')+1);
		$.post( "open/",
			{'csrfmiddlewaretoken': csrf, 
			'address': address,
			'item':item},
			function( data, status ) {
				// DEAL WITH THE DATA HERE
				// I AM MODIFYING THE div WITH id="list" HERE
				$( "#list" ).empty();
				$("#list").append("<div id=\"back\"><button class=\"back_button\" id=\"back_button\" value=\""+data.address+"\">Back</button></div>");
				var content="<ul>";
				$.each(data.file, function(index,element){
					content+="<li><button class=\"file\" value=\""+element+"\">"+element+"</button><button class=\"download\" value=\""+element+"\">Download</button></li>";
				});
				$.each(data.dir, function(index,element){
					content+="<li><button class=\"dir\" value=\""+element+"\">"+element+"</button><button class=\"download\" value=\""+element+"\">Download</button></li>";
				});
				$.each(data.hidden, function(index,element){
					content+="<li><button class=\"dir\" value=\""+element+"\">"+element+"</button><button class=\"download\" value=\""+element+"\">Download</button></li>";
				});
				content+="</ul>";
				$("#list").append(content);
			});
		
	});
	// a general function to manage downloading of the clicked file/directory
	// creates a temporary form and posts it; removes the form later
	// this was a workaround from http://www.developerscoding.com/55/handle-file-download-from-ajax-post
	$(document).on('click','.download',function(){
		var item=$(this).attr("value");
		var curr_path=$('#back_button').attr("value");
		var csrf=$('input[name=csrfmiddlewaretoken]').attr("value");
		// var new_path=(curr_path=="")?item:curr_path+"/"+item;
		// var form = $('<form class="hidden" method="POST" action="">');
  		// form.append($('<input type="hidden" name="name" value="' + new_path + '">'));
  		// form.append($('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'));
  		// form.append($('<input type="hidden" name="action" value="download">'));
  		var form = $('<form class="hidden" method="POST" action="download/">');
        form.append($('<input type="hidden" name="item" value="' + item + '">'));
        form.append($('<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf + '">'));
        form.append($('<input type="hidden" name="address" value="'+curr_path+'">'));
        $('body').append(form);
        form.submit();
        $(".hidden").remove();
	});
});

