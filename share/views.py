#https://stackoverflow.com/questions/3437059/does-python-have-a-string-contains-substring-method
#https://www.quora.com/Whats-the-easiest-way-to-recursively-get-a-list-of-all-the-files-in-a-directory-tree-in-Python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
import os
import mimetypes
import zipfile
from django.conf import settings	#ROOT_DIR, SHARED_DIR, MEDIA_ROOT
import glob
from django.core.files.storage import FileSystemStorage

# Keep CACHE_DIR separate from the shared directory
# Used for storing generated .zip files
CACHE_DIR = os.path.expanduser('~/cache')
SHARED_DIR = getattr(settings, "SHARED_DIR", None)
ROOT_PATH = getattr(settings, "ROOT_PATH", None)
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", None)

def home(request):
	context={}
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
			return ValueError("Invalid mode")

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

		(parentdir,dir_name) = os.path.split(dirpath)
		target = os.path.normpath(CACHE_DIR + dirpath + "/" + dir_name + ".zip")
		
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
			file_to_send = zipfile.ZipFile(target, 'x',zipfile.ZIP_DEFLATED)
			
			for root, dirs, files in os.walk(dirpath):
				for file in files:
					rel_path = os.path.relpath(root,parentdir)
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
		# target - path to requested item
		addr = request.POST["target"]
		addr = os.path.normpath(addr)
		if addr == "" or addr == ".":
			addr = SHARED_DIR

		target = os.path.join(ROOT_PATH, addr)

		if os.path.isdir(target):
			dir_items = os.listdir(target)
			context = {
				"path": addr,
				"dirs": {},
				"files": {},
				"hidden":{}
				}
			for element in dir_items:
				if not element[0] == '.':
					if os.path.isdir(os.path.join(target, element)):
						context["dirs"][os.path.join(addr, element)] = element
					else:
						context["files"][os.path.join(addr, element)] = element
				else:
					context["hidden"][os.path.join(addr, element)] = element

			return JsonResponse(context)

		elif os.path.exists(target):
			return get_file(target, "open")

		else:
			return ValueError("'target' field invalid in request")


# View to handle 'download' requests
@csrf_exempt
def download_item(request):
	if request.method=="POST":
		# find ROOT_PATH from request.user and add login_required decorator

		addr = request.POST["target"]
		addr = os.path.normpath(addr)
		if addr == "" or addr == ".":
			addr = SHARED_DIR

		target = os.path.join(ROOT_PATH, addr)
		if os.path.isdir(target):
			return get_dir(target)
		else:
			return get_file(target, "download")

@csrf_exempt
def upload(request):
    if request.method == 'POST':
        myfile = request.FILES.get('ufile')
        upload_path = request.POST['address']
        upload_path = os.path.join(ROOT_PATH, upload_path)

        fs = FileSystemStorage(location = upload_path)	#directly open the required path
        print(myfile.name)
        filename = fs.save(myfile.name, myfile)
        #os.rename(settings.BASE_DIR + fs.url(filename), os.path.join(ROOT_PATH, upload_path, filename))
        return HttpResponse("")

    else:
        return ValueError("File not found")

def search(request):
    if request.method != "POST":
        return HttpResponseNotFound("Request not sent properly")
    current_path = request.POST['address']
    query = request.POST['query']
    root_path = os.path.expanduser('~')+'/'
    context={
            "dirs":{},
            "files":{},
            "hidden":{}
            }
    print(os.path.join(root_path,current_path))
    for root,directories,files in os.walk(os.path.join(root_path,current_path)):
        for directory in directories:
            if directory.endswith(query):
                context["dirs"][os.path.join(root,directory)]=directory
        for filename in files:
            if query in filename:
                if filename.startswith('.'):
                    file_type="hidden"
                else:
                    file_type="files"
                context[file_type][os.path.join(root,filename)]=filename
    return JsonResponse(context)
