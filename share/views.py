#https://stackoverflow.com/questions/3437059/does-python-have-a-string-contains-substring-method
#https://www.quora.com/Whats-the-easiest-way-to-recursively-get-a-list-of-all-the-files-in-a-directory-tree-in-Python
#https://stackoverflow.com/questions/43013858/ajax-post-a-file-from-a-form-with-axios
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render,redirect
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from ipware.ip import get_ip
import os,subprocess
import mimetypes
import zipfile
# importing models for authentication purpose
from .models import *
import glob
import shutil


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
			IP=get_ip(request)
			t=Token.objects.create(link=key,IP=IP)
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
					new_t=Token.objects.create(link=new_key,IP=IP)
					print(new_t.token)
					request.session['token']=new_t.token
			# When the token is no long valid (i.e expired/deleted from database) but key is valid
			except Token.DoesNotExist:
				request.session.flush()
				key=Key.objects.get(key=k)
				IP='' # get IP from request here
				t=Token.objects.create(link=key,IP=IP)
				request.session['token']=t.token
		request.session.set_expiry(3600) # token expires after 60 minutes
		return redirect('/share/',permanent=True)

@csrf_exempt
def editor_authenticate(request,k):
	if Key.objects.filter(key=k).count()==0:
		return JsonResponse({'message':"The key you provided doesn't exist."},status=404)
	else:
		key=Key.objects.get(key=k)
		if key.permission=='r':
			return JsonResponse({'message':"You don't have editing rights."},status=403)
		IP=get_ip(request)
		t=Token.objects.create(link=key,IP=IP)

		root_path,shared_dir=os.path.split(key.path_shared)
		response_data={}
		response_data['token']=t.token
		response_data['path']=shared_dir
		response_data['files']=[]
		response_data['dirs']=[]
		items=os.listdir(key.path_shared)
		for element in items:
			if os.path.isdir(os.path.join(key.path_shared, element)):
					response_data['dirs'].append(element)
			else:
				response_data['files'].append(element)
		return JsonResponse(response_data)

@csrf_exempt
def editor(request):
	if request.method=="POST":
		if 'token' not in request.POST:
			return JsonResponse({'message':"Invalid request format."},status=404)
		token=request.POST['token']
		if Token.objects.filter(token=token).count()==0:
			return JsonResponse({'message':"Token not identifiable."},status=403)
		else:
			t_Object=Token.objects.get(token=token)
			k_Object=t_Object.link
			sharedPath=k_Object.path_shared
			root_path,shared_dir=os.path.split(sharedPath)
			if request.POST['action']=="open":
				context={}
				context['path']=request.POST['target']
				context['dirs']=[]
				context['files']=[]
				for item in os.listdir(os.path.join(root_path,context['path'])):
					if os.path.isdir(os.path.join(root_path,context['path'],item)):
						context['dirs'].append(item)
					else:
						context['files'].append(item)
				return JsonResponse(context)
			elif request.POST['action']=="download":
				filepath=os.path.join(root_path,request.POST['target'])
				return get_file(filepath,"download")
			elif request.POST['action']=="upload":
				for fname in request.FILES:
					save_path=os.path.join(root_path,os.path.split(fname)[0])
					#if the directories do not exist, create the directories
					if not os.path.exists(save_path):
						os.makedirs(save_path)
					if os.path.exists(os.path.join(root_path,fname)):
						mode=os.stat(os.path.join(root_path,fname)).st_mode
						fs=FileSystemStorage(location=save_path,file_permissions_mode=mode)
						fs.delete(os.path.split(fname)[1])
						fs.save(os.path.split(fname)[1],request.FILES[fname])
					else:
						fs=FileSystemStorage(location=save_path)
						fs.save(os.path.split(fname)[1],request.FILES[fname])
				return JsonResponse({'message':"Save successful."},status=200)
			elif request.POST['action']=="destroy":
				t_Object.delete()
				print("Token deleted.")
			else:
				return JsonResponse({'message':"Invalid request format."},status=404)
	else:
		return JsonResponse({'message':"Invalid request format."},status=404)
			

def home(request):
	if 'token' not in request.session:
		return render(request,'share/error.html',{'title':'Access Denied','header':'Unauthorized access','message':"It seems that the authentication key you provided is invalid.\nObtain the correct link from the host and try again."})
	else:
		return render(request,'share/index.html')
	

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
			return JsonResponse({'message':"Invalid mode!"},status=404)

		response['Content-Length'] = os.path.getsize(filepath)
		return response

	else:
		return JsonResponse({'message':"{0} file does not exist.".format(filepath)},status=403)
	
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
		return JsonResponse({'message':"This directory does not exist."},status=404)

# View to handle 'open' requests
@csrf_exempt
def open_item(request):
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared
	(root_path,shared_dir)=os.path.split(os.path.expanduser(sharedPath))
	# target - path to requested item
	try:
		addr = request.POST["target"]
	except:
		return JsonResponse({'message': 'Invalid request parameters'},status=400)

	addr = os.path.normpath(addr)
	if addr == "" or addr == ".":
		addr = shared_dir
	# To prevent access of directories outside the shared path
	if addr==os.path.join(root_path,addr):
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)

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
		return JsonResponse({'message': 'Unable to ascertain file/folder'},status=500)

# View to handle 'download' requests
@csrf_exempt
def download_item(request):
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared	
	root_path,shared_dir=os.path.split(os.path.expanduser(sharedPath))
	
	try:
		addr = request.POST["target"]
	except:
		return JsonResponse({'message': 'Invalid request parameters'},status=400)

	addr = os.path.normpath(addr)
	if addr == "" or addr == ".":
		addr = shared_dir

	# To prevent access of directories outside the shared path
	if addr==os.path.join(root_path,addr):
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)
	
	target = os.path.join(root_path, addr)

	if os.path.isdir(target):
		return get_dir(target)
	else:
		return get_file(target, "download")

@csrf_exempt
def upload(request):
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared
	root_path,shared_dir=os.path.split(os.path.expanduser(sharedPath))

	can_edit=(Token.objects.get(token=request.session['token']).link.permission=='w')
	if can_edit:
		t_Object=Token.objects.get(token=request.session['token'])
		k_Object=t_Object.link
		#space_available=k_Object.space_allotted-int(subprocess.check_output(['sudo','du','-sb',k_Object.path_shared]).split()[0])
		#print(space_available)
		space_available=400000
		files = request.FILES.getlist('uplist[]')
		total_size = 0
		for myfile in files:
			total_size += myfile.size

		# Checking for available space
		if total_size > space_available:
			return JsonResponse({'message': 'Insufficient space'},status=413)
		
		addresses = request.POST['address[]']

		for address, file in zip(addresses, files):
			directory = os.path.join(sharedPath,address)
			if directory == address:
				return JsonResponse({'message': 'Insufficient priveleges'},status=403)
			
			directory = os.path.dirname(directory)
			#if the directories do not exist, create the directories
			if not os.path.exists(directory):
				os.makedirs(directory)
			
			#if a file with the same name does not exist previously, create the file
			if not os.path.exists(os.path.join(directory,file.name)):
				fs=FileSystemStorage(location=directory)
				fs.save(file.name,file)

		return JsonResponse({'message': 'Success'},status=200);

@csrf_exempt
def search(request):
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared
	root_path,shared_dir=os.path.split(os.path.expanduser(sharedPath))
	try:
		current_path = request.POST['address']
	except:
		return JsonResponse({'message': 'Invalid request parameters'},status=400)
	
	# To prevent access of directories outside the shared path
	if current_path==os.path.join(root_path,current_path):
		return JsonResponse({'message': 'Insufficient priveleges'}, status=403)

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

@csrf_exempt
def delete(request):
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared
	root_path = os.path.dirname(sharedPath)

	try:
		current_path=request.POST['address']
	except:
		return JsonResponse({'message': 'Insufficient priveleges'},status=400)
	
	directory = os.path.join(root_path, current_path)
	if os.path.isdir(directory):
		shutil.rmtree(directory)
	elif os.path.isfile(directory):
		os.remove(directory)
	else:
		return JsonResponse({'message': 'Unable to ascertain file/folder'},status=403)

	return JsonResponse({'message':'Success'}, status=200)

@csrf_exempt
def create_folder(request):
	sharedPath = Token.objects.get(token=request.session['token']).link.path_shared	
	root_path = os.path.dirname(sharedPath)
	can_edit=(Token.objects.get(token=request.session['token']).link.permission=='w')
	if can_edit:
		
		try:
			current_path=request.POST['address']
			folder = request.POST['folder_name']
		except:
			return JsonResponse({'message': 'Invalid parameters'},status=403)
		
		if current_path==os.path.join(root_path, current_path):
			return JsonResponse({'message': 'Insufficient priveleges'},status=403)
		
		directory = os.path.join(root_path, current_path)
		
		if folder==os.path.join(directory, folder):
			return JsonResponse({'message': 'Folder already exists'},status=403)
		
		directory = os.path.join(directory, folder)
		if not os.path.exists(directory):
			os.makedirs(directory)
			return JsonResponse({'message':'Success'}, status=200)
	else:
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)

@csrf_exempt
def move(request):
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared	
	root_path = os.path.dirname(sharedPath)

	try:
		source_path=request.POST['source_address']
		target_path=request.POST['target_address']
		#source = request.POST['source_name']
		target = request.POST['target_name']
	except:
		return JsonResponse({'message': 'Invalid parameters'},status=403)

	source_path = os.path.join(root_path, source_path)
	#source_path = os.path.join(source_path,source)
	target_path = os.path.join(root_path, target_path)
	target_path = os.path.join(target_path,target)

	if not os.path.exists(target_path):
		shutil.move(source_path,target_path)
		return JsonResponse({'message':'Success'}, status=200)
	else:
		return JsonResponse({'message': 'Destination already exists'},status=403)
