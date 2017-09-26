# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.core.files import File
import os
import mimetypes

# Create your views here.
def home(request):
	root_path="/home/yash/Public"
	if not request.method=="POST":
		current_path=""
		curr_dir_items=os.listdir(os.path.join(root_path,current_path))
		curr_dir={}
		for item in curr_dir_items:
			if not item[0]=='.':
				if(os.path.isdir(os.path.join(root_path,current_path,item))):
					curr_dir[item]="dir"
				else:
					curr_dir[item]="file"

		context={'list':curr_dir,'current_path':current_path}
		return render(request,'Server/index.html',context)
	else:
		current_path=""
		for name in request.POST:
			if not name=="csrfmiddlewaretoken":
				current_path=name+"/"
				break

		if os.path.isdir(os.path.join(root_path,current_path)):
			curr_dir_items=os.listdir(os.path.join(root_path,current_path))
			if curr_dir_items:
				curr_dir={}
				for item in curr_dir_items:
					if not item[0]=='.':
						if(os.path.isdir(os.path.join(root_path,current_path,item))):
							curr_dir[item]="dir"
						else:
							curr_dir[item]="file"

				context={'list':curr_dir,'current_path':current_path}
				return render(request,'Server/index.html',context)
			else:
				return HttpResponse("This directory is empty")
		else:
			return get_file(request)

# View to handle file download requests
def get_file(request):
	root_path="/home/yash/Public"
	if request.method=='POST':
		filepath=None
		for name in request.POST:
			if not name=="csrfmiddlewaretoken":
				filepath=name
				break
		# http://voorloopnul.com/blog/serving-large-and-small-files-with-django/
		filepath=os.path.join(root_path,filepath)
		if os.path.exists(filepath):
			response = StreamingHttpResponse((line for line in open(filepath,'r')))
			response['Content-Disposition'] = " attachment; filename={0}".format(os.path.basename(filepath))
			#response['Conetent-Type'] = mimetypes.guess_type(filepath)[0]
			response['Content-Length'] = os.path.getsize(filepath)
			return response
		else:
			return HttpResponse("This file does not exist")
	else:
		return HttpResponse("Invalid request!")	