# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse, JsonResponse
from django.core.files import File
from django.views.decorators.csrf import csrf_exempt
from django.template import loader
import os,binascii
import mimetypes
import zipfile
# importing models for authentication purpose
from .models import *

# (root_path, shared_dir) = os.path.split(os.path.expanduser('~/Public'))

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
			print(t.token)
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
					# del request.session['token']
					request.session.flush()
					new_t=Token.objects.create(link=new_key,ip=IP)
					print(new_t.token)
					request.session['token']=new_t.token
			# When the token is no long valid (i.e expired/deleted from database) but key is valid
			except Token.DoesNotExist:
				request.session.flush()
				key=Key.objects.get(key=k)
				IP='' # get IP from request here
				t=Token.objects.create(link=key,ip=IP)
				print(t.token)
				request.session['token']=t.token
		request.session.set_expiry(1800) # token expires after 30 minutes
		print(request.session['token'])
		return redirect('/share/',permanent=True)

def home(request):
	if 'token' not in request.session:
		return render(request,'share/error.html',{'title':'Access Denied','header':'Unauthorized access','message':"It seems that the authentication key you provided is invalid.\nObtain the correct link from the host and try again."})
	else:
		print(request.session['token'])
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
	sharedPath=None
	if request.method == "POST":
		if 'token' not in request.POST:
			return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
		elif Token.objects.filter(token=request.POST['token']).count()==0:
			return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
		sharedPath=Token.objects.get(token=request.POST['token']).link.path_shared
	else:
		if 'token' not in request.session:
			return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
		elif Token.objects.filter(token=request.POST['token']).count()==0:
			return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
		sharedPath=Token.objects.get(token=request.POST['token']).link.path_shared

	if sharedPath!=None:
		(root_path,shared_dir)=os.path.split(os.path.expanduser(sharedPath))
		# target - path to requested item
		addr = request.POST["target"]
		addr = os.path.normpath(addr)
		if addr == "" or addr == ".":
			addr = shared_dir

		target = os.path.join(root_path, addr)

		if os.path.isdir(target):
			dir_items = os.listdir(target)
			context = {
				"path": addr,
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

		elif os.path.exists(target):
			return get_file(target, "open")

		else:
			# return ValueError("'target' field invalid in request")
			return JsonResponse({'status':'false','message':"Could not resolve 'target'."}, status=500)


# View to handle 'download' requests
@csrf_exempt
def download_item(request):
	if request.method=="POST":
		if not request.POST.get('token',None):
			return ValueError("Unauthorized access detected.")
		elif Token.objects.filter(token=request.POST['token']).count()==0:
			return ValueError("Token is unidentifiable.")

		sharedPath=Token.objects.get(token=request.POST['token']).link.path_shared	
		(root_path,shared_dir)=os.path.split(os.path.expanduser(sharedPath))

		addr = request.POST["target"]
		addr = os.path.normpath(addr)
		if addr == "" or addr == ".":
			addr = shared_dir

		target = os.path.join(root_path, addr)
		if os.path.isdir(target):
			return get_dir(target)
		else:
			return get_file(target, "download")

