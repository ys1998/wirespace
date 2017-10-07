# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse, JsonResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
import os
import mimetypes
import zipfile

# Cache is stored in this location
# Keep it different from the shared directory
root_path=os.path.expanduser('~')
CACHE_DIR=root_path+'/cache'

# Create your views here.
def home(request):
	# Displaying the initial directory structure

	# if not request.method=="POST":
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
	return render(request,'share/index.html',context)

# View to handle file download requests
def get_file(filepath,mode):
	# http://voorloopnul.com/blog/serving-large-and-small-files-with-django/
	if os.path.exists(filepath):
		response = StreamingHttpResponse(
			open(filepath,'rb'),
			content_type = mimetypes.guess_type(filepath)[0]
			)

		if mode == "open":
			response['Content-Disposition'] = " inline; filename={0}".format(os.path.basename(filepath))
		elif mode == "download":
			response['Content-Disposition'] = " attachment; filename={0}".format(os.path.basename(filepath))
		else:
			return ValueError("Invalide mode")
		
		response['Content-Length'] = os.path.getsize(filepath)
		return response

	else:
		return HttpResponse("{0} file does not exist.".format(filepath))
	
# View to handle directory download requests
# CACHE_DIR is used for storing generated .zip files for future use - 
# prevents them for being created multiple times
def get_dir(dirpath):
	global CACHE_DIR
	if not os.path.exists(CACHE_DIR):
		os.makedirs(CACHE_DIR)

	if os.path.isdir(dirpath):
		if not os.path.exists(CACHE_DIR+dirpath):
			os.makedirs(CACHE_DIR+dirpath)

		(dir_name, parentdir) = os.path.split(dirpath)
		target = CACHE_DIR + dirpath + "/" + dir_name + ".zip"
		# checking if required .zip file already exists in CACHE_DIR 
		if os.path.exists(target):
			response = StreamingHttpResponse(
				open(target,'rb'),
				content_type='application/x-gzip'
				)
			response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
			response['Content-Length'] = os.path.getsize(target)
			return response
		# creating new .zip file if not already created 
		else:
			file_to_send = zipfile.ZipFile(
				target, zipfile.ZIP_DEFLATED)

			for root, dirs, files in os.walk(dirpath):
				for file in files:
					rel_path = os.path.relpath(root, parentdir)
					file_to_send.write(
						os.path.join(root,file),
						os.path.join(rel_path,file)
						)

			file_to_send.close()
			response = StreamingHttpResponse(
				open(target,'rb'),
				content_type = 'application/x-gzip')
			response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
			response['Content-Length'] = os.path.getsize(target)
			return response
	else:
		return HttpResponse("This directory does not exist.")

# View to handle 'open' requests
@csrf_exempt
def open_item(request):
	if request.method == "POST":
		# 2 fields:
		# target - path to requested item
		# absolute - bool for whether path is absolute
		target = request.POST["target"]
		isAbs = request.POST["absolute"].lower()
		if isAbs == 'false':
			target = os.path.join(root_path, target)
		elif isAbs == 'true':
			target = target
		else :
			raise ValueError
		# find root_path from request.user and add login_required decorator
		
		if os.path.isdir(target):
			dir_items = os.listdir(target)
			context = {
				"address": target,
				"dirs": [],
				"files": [],
				"hidden":[]
				}
			for element in dir_items:
				if not element[0] == '.':
					if os.path.isdir(os.path.join(target, element)):
						context["dirs"].append(element)
					else:
						context["files"].append(element)
				else:
					context["hidden"].append(element)

			return JsonResponse(context)

		else:
			return get_file(target, "open")


# View to handle 'download' requests
def download_item(request):
	if request.method=="POST":
		# find root_path from request.user and add login_required decorator

		target = request.POST["target"]
		isAbs = request.POST["absolute"].lower()
		if isAbs == 'false':
			target = os.path.join(root_path, target)
		elif isAbs == 'true':
			target = target
		else :
			raise ValueError

		if os.path.isdir(target):
			return get_dir(target)
		else:
			return get_file(target, "download")

