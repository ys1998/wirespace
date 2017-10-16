#https://stackoverflow.com/questions/3437059/does-python-have-a-string-contains-substring-method
#https://www.quora.com/Whats-the-easiest-way-to-recursively-get-a-list-of-all-the-files-in-a-directory-tree-in-Python
#https://stackoverflow.com/questions/43013858/ajax-post-a-file-from-a-form-with-axios
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,redirect
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
import os
import mimetypes
import zipfile
# importing models for authentication purpose
from .models import *
import glob
from django.core.files.storage import FileSystemStorage
from django.contrib.sessions.models import Session


# Keep CACHE_DIR separate from the shared directory
# Used for storing generated .zip files
CACHE_DIR = os.path.expanduser('~/cache')

def authenticate(request,k):
	# use request.sessions['token']
	if Key.objects.filter(key=k).count()==0:
		return render(request,'share/error.html',{'title':'Access Denied','header':'You don\'t have access','message':'It seems that the authentication key you provided is invalid.\nObtain the correct link from the host and try again.'})
	else:
		# Token doesn't exist but key is valid
		if 'token' not in request.session:
			key=Key.objects.get(key=k)
			IP='' # get IP from request here
			t=Token.objects.create(link=key,ip=IP)
			request.session['token']=t.token
		else:
			# Token exists in request.session
			try:
				# When the key is valid but the existing token refers to a different valid key
				old_t=Token.objects.get(token=request.session['token'])
				old_key=old_t.link.key
				if k!=old_key:
					new_key=Key.objects.get(key=k)
					IP=''
					old_t.delete()
					del request.session['token']
					new_t=Token.objects.create(link=new_key,ip=IP)
					print(new_t.token)
					request.session['token']=new_t.token
			# When the token is no long valid (i.e expired/deleted from database) but key is valid
			except Token.DoesNotExist:
				request.session.flush()
				key=Key.objects.get(key=k)
				IP='' # get IP from request here
				t=Token.objects.create(link=key,ip=IP)
				request.session['token']=t.token
		request.session.set_expiry(1800) # token expires after 30 minutes
		return redirect('/share/',permanent=True)

def home(request):
	if 'token' not in request.session:
		return render(request,'share/error.html',{'title':'Access Denied','header':'Unauthorized access','message':"It seems that the authentication key you provided is invalid.\nObtain the correct link from the host and try again."})
	else:
		return render(request,'share/index.html',{'token':request.session.get('token')})
	

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
		# Add another check : whether contents of that dir have been updated after the .zip was created
		if os.path.exists(target):
			response = StreamingHttpResponse(
				open(target,'rb'),
				content_type='application/x-gzip'
				)
			response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
			response['Content-Length'] = os.path.getsize(target)
			return response
		# creating new .zip file if not already created
		# if .zip has to be updated, remove existing .zip file and create new one in its place
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
	sharedPath=None
	if request.method == "POST":
		token=None
		if request.session['token']:
			token=request.session['token']
		if token is None:
			return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
		elif Token.objects.filter(token=token).count()==0:
			return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
		sharedPath=Token.objects.get(token=token).link.path_shared
		if sharedPath!=None:
			(root_path,shared_dir)=os.path.split(os.path.expanduser(sharedPath))
			# target - path to requested item
			addr = request.POST["target"]
			addr = os.path.normpath(addr)
			if addr == "" or addr == ".":
				addr = shared_dir

			# To prevent access of directories outside the shared path
			if addr in root_path:
				addr=root_path
			target = os.path.join(root_path, addr)

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
				return JsonResponse({'status':'false','message':"Could not resolve 'target'."}, status=500)
		else:
			return JsonResponse({'status':'false','message':"Shared path uninitialized."}, status=500)
	else:
		return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)


# View to handle 'download' requests
@csrf_exempt
def download_item(request):
	sharedPath=None
	if request.method == "POST":
		token=None
		if request.session['token']:
			token=request.session['token']
		if token is None:
			return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
		elif Token.objects.filter(token=token).count()==0:
			return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
		
		sharedPath=Token.objects.get(token=token).link.path_shared	
		root_path,shared_dir=os.path.split(os.path.expanduser(sharedPath))
		
		addr = request.POST["target"]
		addr = os.path.normpath(addr)
		if addr == "" or addr == ".":
			addr = shared_dir

		if addr in root_path:
			addr=root_path
		target = os.path.join(root_path, addr)

		if os.path.isdir(target):
			return get_dir(target)
		else:
			return get_file(target, "download")
	else:
		return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)

@csrf_exempt
def upload(request):
	sharedPath=None
	if request.method == "POST":
		token=None
		if request.session['token']:
			token=request.session['token']
		if token is None:
			return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
		elif Token.objects.filter(token=token).count()==0:
			return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
		
		sharedPath=Token.objects.get(token=token).link.path_shared
		can_upload=(Token.objects.get(token=token).link.permission=='w')
		root_path,shared_dir=os.path.split(os.path.expanduser(sharedPath))
		if can_upload:
			myfile=request.FILES.get('ufile')
			upload_path = request.POST['address']
			upload_path=os.path.normpath(upload_path)
			
			if upload_path in root_path:
				upload_path=root_path
			
			upload_path = os.path.join(root_path, upload_path)
			# directly open the required path
			fs=FileSystemStorage(location=upload_path)
			filename=fs.save(myfile.name,myfile)
			return HttpResponse('')
		else:
			return JsonResponse({'status':'false','message':"Upload prohibited."}, status=403)
	else:
		return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)

@csrf_exempt
def search(request):
	if request.method != "POST":
		return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)
	else:
		token=None
		if request.session['token']:
			token=request.session['token']
		if token is None:
			return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
		elif Token.objects.filter(token=token).count()==0:
			return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
		
		sharedPath=Token.objects.get(token=token).link.path_shared
		root_path,shared_dir=os.path.split(os.path.expanduser(sharedPath))
		current_path = request.POST['address']
		query = request.POST['query']

		context={"dirs":{},"files":{},"hidden":{}}

		for root,directories,files in os.walk(os.path.join(root_path,current_path)):
			for directory in directories:
				if query in directory:
					rel_path=s=os.path.relpath(root,root_path)
					context["dirs"][os.path.join(rel_path,directory)]=directory
			for filename in files:
				if query in filename:
					if filename.startswith('.'):
						file_type="hidden"
					else:
						file_type="files"
					rel_path=os.path.relpath(root,root_path)
					context[file_type][os.path.join(rel_path,filename)]=filename
		return JsonResponse(context)

