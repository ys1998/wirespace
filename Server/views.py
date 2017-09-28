# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.core.files import File
import os
import mimetypes
import zipfile

# Cache is stored in this location
# Keep it different from the shared directory
CACHE_DIR='/home/yash/cache'

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
		action=None
		current_path=""
		for name in request.POST:
			if not name=="csrfmiddlewaretoken":
				action=name.split(':')[0]
				current_path=name.split(':')[1]+"/"
				break
		if action=="open":
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
				return get_file(str(os.path.join(root_path,current_path))[:-1],"open")
		elif action=="download":
			if os.path.isdir(os.path.join(root_path,current_path)):
				return get_dir(str(os.path.join(root_path,current_path))[:-1],"/".join(os.path.join(root_path,current_path).split('/')[:-2]))
			else:
				return get_file(str(os.path.join(root_path,current_path))[:-1],"download")


# View to handle file download requests
def get_file(filepath,mode):
	# http://voorloopnul.com/blog/serving-large-and-small-files-with-django/
	if os.path.exists(filepath):
		response = StreamingHttpResponse(open(filepath,'rb'),content_type=mimetypes.guess_type(filepath)[0])
		if mode=="open":
			response['Content-Disposition'] = " inline; filename={0}".format(os.path.basename(filepath))
		elif mode=="download":
			response['Content-Disposition'] = " attachment; filename={0}".format(os.path.basename(filepath))
		response['Content-Length'] = os.path.getsize(filepath)
		return response
	else:
		return HttpResponse("{0} file does not exist.".format(filepath))
	
# # View to handle directory download requests
def get_dir(dirpath,rootpath):
	global CACHE_DIR
	if not os.path.exists(CACHE_DIR):
		os.makedirs(CACHE_DIR)
	if os.path.isdir(dirpath):
		dir_name=dirpath.split('/')[-1]
		# checking if required .zip file already exists in CACHE_DIR 
		if os.path.exists(CACHE_DIR+dirpath+"/"+dir_name+".zip"):
			response = StreamingHttpResponse(open(CACHE_DIR+dirpath+"/"+dir_name+".zip",'rb'),content_type='application/x-gzip')
			response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
			response['Content-Length'] = os.path.getsize(CACHE_DIR+dirpath+"/"+dir_name+".zip")
			return response
		# creating new .zip file if not already created 
		else:
			os.makedirs(CACHE_DIR+dirpath)
			file_to_send=zipfile.ZipFile(CACHE_DIR+dirpath+"/"+dir_name+".zip",'w',zipfile.ZIP_DEFLATED)
			for root,dirs,files in os.walk(dirpath):
				for file in files:
					rel_path=os.path.relpath(root,rootpath)
					file_to_send.write(os.path.join(root,file),os.path.join(rel_path,file))
			file_to_send.close()
			response = StreamingHttpResponse(open(CACHE_DIR+dirpath+"/"+dir_name+".zip",'rb'),content_type='application/x-gzip')
			response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
			response['Content-Length'] = os.path.getsize(CACHE_DIR+dirpath+"/"+dir_name+".zip")
			return response
	else:
		return HttpResponse("This directory does not exist.")
