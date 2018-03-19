## @file views.py
#
# This file contains the definitions of all the functions required by the project.
from __future__ import unicode_literals
from django.shortcuts import render,redirect
from django.http import HttpResponse, StreamingHttpResponse, JsonResponse
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from ipware.ip import get_ip
# for moving,deleting and creating new files/folders
from django.core.files.storage import FileSystemStorage
import os,shutil,subprocess
# for downloading files/folders
import mimetypes
import zipfile
import random
# importing models for authentication purpose
from .models import *

# Keep CACHE_DIR separate from the shared directory
## Used for storing generated .zip files
CACHE_DIR='/tmp/wirespace/cache'

## @brief View to handle one-time authentication for the current session.
#
# Checks if the correct key has been provided and then creates a token which expires after 60 minutes.
# @param request Instance of HttpRequest containing required meta-data
# @param k The key passed by the client
# @returns Depending on the success of the authentication, an error message is displayed or the page is redirected to share/
def authenticate(request,k):
	
	# use request.sessions['token']
	if Key.objects.filter(key=k).count()==0:
		return render(
			request,
			'share/error.html',
			{
				'title':'Access Denied',
				'header':'You don\'t have access',
				'message':'It seems that the authentication key you provided is invalid.\nObtain the correct link from the host and try again.'
			}
		)
	else:
		# Token does not exist but the key is valid
		if 'token' not in request.session:
			key = Key.objects.get(key=k)
			IP = get_ip(request)
			t = Token.objects.create(link=key, IP=IP)
			request.session['token']=t.token
		else:
			# Token exists in request.session
			try:
				# When the key is valid but the existing token refers to a different valid key
				old_token = Token.objects.get(token=request.session['token'])
				old_key = old_token.link.key
				if not k == old_key:
					new_key = Key.objects.get(key=k)
					IP = get_ip(request)
					old_token.delete()
					del request.session['token']
					new_token = Token.objects.create(link=new_key,IP=IP)
					#print(new_t.token)
					request.session['token'] = new_token.token
			# When the token is no long valid (i.e expired/deleted from database) but key is valid
			except Token.DoesNotExist:
				request.session.flush()
				key = Key.objects.get(key=k)
				IP = get_ip(request)
				token = Token.objects.create(link=key, IP=IP)
				request.session['token'] = token.token

		request.session.set_expiry(3600) 				# Token expires after 60 minutes
		return redirect('/share/',permanent=True)

##	@brief View to handle authentication for the file editor.
#
#	If the user has write permission and a correct key has been provided, the client is provided a unique token and a list of editable files.
#	@param request Instance of HttpRequest containing required meta-data
#	@param k The key passed by the client
#	@returns A JsonResponse object containing an error message, or a unique token and a list of files and directories for editing
@csrf_exempt
def editor_authenticate(request,k):
	if Key.objects.filter(key=k).count() == 0:
		return JsonResponse({'message':"The key you provided doesn't exist."}, status=404 )
	else:
		key = Key.objects.get(key=k)
		if key.permission == 'r':
			return JsonResponse({'message':"You don't have editing rights."}, status=403)
		IP = get_ip(request)
		token = Token.objects.create(link=key, IP=IP)

		root_path,shared_dir=os.path.split(key.path_shared)
		response_data={
			'token': token.token,
			'path': shared_dir,
			'files': [],
			'dirs': []
		}
		items = os.listdir(key.path_shared)
		for element in items:
			if os.path.isdir(os.path.join(key.path_shared, element)):
					response_data['dirs'].append(element)
			else:
				response_data['files'].append(element)
		return JsonResponse(response_data)

##	@brief View for handling the save, download, upload and editing features of the editor
#
#	Validates token and then performs different actions depending on the mode. These include serving file for editing, sending list of editable files, updating the edited file on the host's machine and destroying the associated token.
#	@param request Instance of HttpRequest containing required meta-data
#	@returns A JsonResponse object containing a success or error message and relevant data
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
			can_edit=(k_Object.permission=="w")
			if can_edit:
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
				return JsonResponse({'message': 'Insufficient priveleges'},status=403)
	else:
		return JsonResponse({'message':"Invalid request format."},status=404)
			
##	@brief View for opening the homepage. (/share/)
#	
#	@param request Instance of HttpRequest containing required meta-data
def home(request):

	if 'token' not in request.session:
		return render(
			request,
			'share/error.html',
			{
				'title':'Access Denied',
				'header':'Unauthorized access',
				'message':"It seems that the authentication key you provided is invalid.\nObtain the correct link from the host and try again."
			}
		)
	else:
		return render(request, 'share/index.html')
	

##	@brief Function that downloads/opens the required file as per the request.
#
#	Guesses the file type using mimetypes and then sets the 'Content-disposition' according to the request and sends back the response. If at any time, any error occurs, an error message is displayed.
#	@param filepath The full path of the file to be accessed
#	@param mode Specifies whether the file has to be downloaded or opened in the browser
#	@returns A StreamingHttpResponse object if no error occured, or a JsonResponse object otherwise
def get_file(filepath, mode):
	
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
			return JsonResponse({'message':"Invalid mode!"}, status=404)

		response['Content-Length'] = os.path.getsize(filepath)
		return response

	else:
		return JsonResponse({'message':"{0} file does not exist.".format(filepath)}, status=403)
	
##	@brief Function to download the specified directory
#
#	Compresses the directory into a zip file and returns a StreamingHttpResponse object. CACHE_DIR is not maintained
#	@param dirpath the full path of the directory to be accessed
#	@returns A StreamingHttpResponse if no error occured, and a JsonResponse object otherwise
def get_dir(dirpath):

	# global CACHE_DIR
	# if not os.path.exists(CACHE_DIR):
	# 	os.makedirs(CACHE_DIR)
	if os.path.isdir(dirpath):
	 	target = dirpath
	 	file_to_send = zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED)
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
			content_type = 'application/x-gzip'
			)
	 	response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
	 	response['Content-Length'] = os.path.getsize(target)
	 	os.remove(target)
	 	return response
	else:
		return JsonResponse({'message':"This directory does not exist."}, status=404)
	# 	if not os.path.exists(CACHE_DIR+dirpath):
	# 		os.makedirs(CACHE_DIR+dirpath)

	# 	(parentdir,dir_name) = os.path.split(dirpath)
	# 	target = os.path.normpath(CACHE_DIR + dirpath + "/" + dir_name + ".zip")
		
	# 	# checks for existing .zip file and removes it if it exists (the file might have been edited between the time is was last downloaded and the current request)
	# 	if os.path.exists(target):
	# 		# response = StreamingHttpResponse(
	# 		# 	open(target,'rb'),
	# 		# 	content_type='application/x-gzip'
	# 		# 	)
	# 		# response['Content-Disposition'] = " attachment; filename={0}".format(dir_name+".zip")
	# 		# response['Content-Length'] = os.path.getsize(target)
	# 		# return response
	#		os.remove(target)
		# creates new .zip file
		

		#setting the HttpResponse
		

##	@brief View to handle opening of the selected directory/file
#
#	The code checks if the target is a directory or a file. If it is a file, it redirects to the \a get_file function; otherwise it creates a dictionary of a list of contents in the directory and sends back the data as a JsonResponse object
#	@param request POST request containing the address of the target to be opened
#	@returns A JsonResponse containing a list of files and folders present in the directory
def open_item(request):

	sharedPath = Token.objects.get(token=request.session['token']).link.path_shared
	(root_path,shared_dir) = os.path.split(os.path.expanduser(sharedPath))
	# target - path to requested item
	try:
		addr = request.POST["target"]
	except:
		return JsonResponse({'message': 'Invalid request parameters'},status=400)

	addr = os.path.normpath(addr)
	if addr == "" or addr == ".":
		addr = shared_dir
	# To prevent access of directories outside the shared path
	if addr == os.path.join(root_path,addr):
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)

	#check if the specified target is a directory and then populate the file list
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
	
	#if it is a file, call get_file
	elif os.path.exists(target):
		return get_file(target, "open")
	else:
		return JsonResponse({'message': 'Unable to ascertain file/folder'},status=500)

##	@brief View to download all/selected content of the current directory
#
#	If the directory contains just one item, the request is forwarded to the appropriate functions(\a get_dir or \a get_file). Otherwise, it creates a .zip file of the contents of the directory.
#	Note: Hidden files are not sent via this method.
#	@param request POST request containing the target list.
#	@returns A StreamingHttpResponse object containing a zip file or a single file depending on the request
def download_item(request):
	
	sharedPath = Token.objects.get(token=request.session['token']).link.path_shared	
	root_path,shared_dir = os.path.split(os.path.expanduser(sharedPath))
	
	try:
		addr = request.POST.getlist("target[]")
		addr = list(set(addr))
	except:
		return JsonResponse({'message': 'Invalid request parameters'}, status=400)
	
	if len(addr) == 1:
		# If only a single object is to be downloaded
		addr = addr[0]
		addr = os.path.normpath(addr)
		if addr == "" or addr == ".":
			addr = shared_dir

		# To prevent access of directories outside the shared path
		if addr == os.path.join(root_path,addr):
			return JsonResponse({'message': 'Insufficient priveleges'},status=403)
		
		target = os.path.join(root_path, addr)

		if os.path.isdir(target):
			return get_dir(target)
		else:
			return get_file(target, "download")
	
	else:
		# Download multiple objects simultaneously
		print(addr)
		new_addr = [item.strip() for item in addr if item.strip() != "" or item.strip() != "." or item.strip() != ".."]
		curr_dir = os.path.basename(os.path.split(new_addr[0])[0])

		print(curr_dir)
		target = curr_dir + str(random.randint(10000000, 99999999)) + "-partial.zip"
		print(target)
		file_to_send = zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED)

		for item in new_addr:
			if os.path.isdir(os.path.join(root_path,item)):
				curr_path=os.path.split(item)[0]
				for root, dirs, files in os.walk(os.path.join(root_path,item)):
					for file in files:
						rel_path = os.path.relpath(root,os.path.join(root_path,curr_path))
						file_to_send.write(
							os.path.join(root,file),
							os.path.join(rel_path,file)
							)
			else:
				file_to_send.write(
					os.path.join(root_path,item),
					os.path.join(os.path.basename(item)),
					)
		print(file_to_send.testzip())
		file_to_send.close()
		# Setting and sending the response
		response = StreamingHttpResponse(
			open(target, 'rb'),
			content_type = 'application/x-gzip'
			)
		response['Content-Disposition'] = " attachment; filename={0}".format(target)
		response['Content-Length'] = os.path.getsize(target)
		os.remove(target)
		return response


##	@brief View to upload a file or folder from the client
#	
#	Checks if sufficient storage space is present and whether the client has editing rights. If the target path exists, the file is directly placed at the specified target. Otherwise, the target is first created and then the file is placed in it.
#	@param request POST request containing files with their addresses
#	@returns A JsonResponse object containing a success or error message.
def upload(request):

	sharedPath = Token.objects.get(token=request.session['token']).link.path_shared
	root_path, shared_dir = os.path.split(os.path.expanduser(sharedPath))

	#check if the client has write permission or not
	can_edit = (Token.objects.get(token=request.session['token']).link.permission=='w')
	
	if can_edit:
		t_Object = Token.objects.get(token=request.session['token'])
		k_Object = t_Object.link
		
		#available space is the unallocated space on the server
		#du does not work on Mac, so temporarily setting the available space to 0.4 GB
		#space_available=k_Object.space_allotted-int(subprocess.check_output(["du","-s",k_Object.path_shared]).split()[0])
		
		space_available=400000000
		files = request.FILES.getlist('uplist[]')
		total_size = 0
		for myfile in files:
			total_size += myfile.size

		# Checking for available space
		if total_size > space_available:
			return JsonResponse({'message': 'Insufficient space'}, status=413)
		#print(files)
		addresses = request.POST.getlist('address[]')
		
		for address, file in zip(addresses, files):
			directory = os.path.join(root_path,address)
			
			if directory == address:
				return JsonResponse({'message': 'Insufficient priveleges'}, status=403)
			directory = os.path.dirname(directory)

			#if the directories do not exist, create the directories
			if not os.path.exists(directory):
				os.makedirs(directory)
			
			#if a file with the same name does not exist previously, create the file
			if not os.path.exists(os.path.join(directory,file.name)):
				fs=FileSystemStorage(location=directory)
				fs.save(file.name,file)
		#send a success message on successful upload
		return JsonResponse({'message': 'Success'},status=200);
	else:
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)

##	@brief View to search the current directory recursively for a file or folder
#	
#	Iterates through each file and directory recursively and checks if they contain the required substring. All hits (including hidden files) are returned as a JsonResponse object
#	@param request POST request containing the address of the directory to be searched and the search query
#	@returns A JsonResponse object containing a list of all files and directories having the query in their name
def search(request):

	sharedPath = Token.objects.get(token=request.session['token']).link.path_shared
	root_path,shared_dir = os.path.split(os.path.expanduser(sharedPath))
	try:
		current_path = request.POST['address']
	except:
		return JsonResponse({'message': 'Invalid request parameters'}, status=400)
	
	# To prevent access of directories outside the shared path
	if current_path == os.path.join(root_path, current_path):
		return JsonResponse({'message': 'Insufficient priveleges'}, status=403)
	
	#get the query from the request
	query = request.POST['query']

	context = {
		"dirs": {},
		"files": {},
		"hidden": {}
		}

	#search all the subdirectories and files
	for root,directories,files in os.walk(os.path.join(root_path,current_path)):
		for directory in directories:
			if query in directory:
				rel_path = os.path.relpath(root,root_path)
				context["dirs"][os.path.join(rel_path,directory)] = directory
		for filename in files:
			if query in filename:
				if filename.startswith('.'):
					file_type = "hidden"
				else:
					file_type = "files"
				rel_path = os.path.relpath(root,root_path)
				context[file_type][os.path.join(rel_path,filename)] = filename
	return JsonResponse(context)

##	@brief View to handle deletion of a file or folder on the server via a request from the client
#
#	If the client has write priviledges, it checks if the target is a file or folder and then deletes it PERMANENTLY using respective python functions.
#	@param request POST request containing the address of the target to be deleted
#	@returns A success or error message as a JsonResponse object
def delete(request):
	
	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared
	root_path = os.path.dirname(sharedPath)
	can_edit=(Token.objects.get(token=request.session['token']).link.permission=='w')
	if can_edit:
		try:
			current_paths = request.POST.getlist('address[]')
		except:
			return JsonResponse({'message': 'Invalid parameters'},status=400)
		
		directory = os.path.join(root_path, current_path)
		if directory == current_path:
			return JsonResponse({'message': 'Insufficient priveleges'},status=400)
		#if the target is a directory, remove all it's contents recursively
		if os.path.isdir(directory):
			shutil.rmtree(directory)
		#if the target is a file, os.remove is sufficient
		elif os.path.isfile(directory):
			os.remove(directory)
		else:
			return JsonResponse({'message': 'Unable to ascertain file/folder'},status=403)
		for current_path in current_paths:
			directory = os.path.join(root_path, current_path)
			if directory == current_path:
				return JsonResponse({'message': 'Insufficient priveleges'},status=400)
			if os.path.isdir(directory):
				shutil.rmtree(directory)
			elif os.path.isfile(directory):
				os.remove(directory)
			else:
				return JsonResponse({'message': 'Unable to ascertain file/folder'},status=403)

		return JsonResponse({'message':'Success'}, status=200)
	else:
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)

##	@brief View to create a new folder with a specified name
#	
#	If the folder does not exist previously, a new folder is created with the required name (The functionality is similar to mkdir -p). Also, entering incorrect folder names will not do anything.
#	@param request POST request containing the name of the folder to be created and its address
#	@returns A JsonResponse object denoting success or failure of the action
def create_folder(request):

	sharedPath = Token.objects.get(token=request.session['token']).link.path_shared	
	root_path = os.path.dirname(sharedPath)
	can_edit=(Token.objects.get(token=request.session['token']).link.permission=='w')
	if can_edit:
		
		try:
			current_path=request.POST['address']
			folder = request.POST['folder_name']
		except:
			return JsonResponse({'message': 'Invalid parameters'},status=400)
		
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

##	@brief A generic function for moving a file/directory from one place to another (can also be used for renaming)
#	
#	If the client has write permission and the destination does not already exist, the files/folders are moved to the appropriate place. Otherwise, an error message is returned.
#	@param request POST request containing the source and target addresses
#	@returns A message signifying whether the move was successful or not as a JsonResponse object.
def move(request):

	sharedPath=Token.objects.get(token=request.session['token']).link.path_shared	
	root_path = os.path.dirname(sharedPath)
	can_edit=(Token.objects.get(token=request.session['token']).link.permission=='w')
	if can_edit:
		try:
			source=request.POST['source']
			target=request.POST['target']
		except:
			return JsonResponse({'message': 'Invalid parameters'},status=400)

		source_path = os.path.join(root_path, source)
		target_path = os.path.join(root_path, target)

		if source_path == source or target_path == target:
			return JsonResponse({'message': 'Insufficient priveleges'},status=403)

		try:
			shutil.move(source_path,target_path)
			return JsonResponse({'message':'Success'}, status=200)
		except:
			return JsonResponse({'message': 'Destination already exists'},status=403)
	else:
		return JsonResponse({'message': 'Insufficient priveleges'},status=403)
