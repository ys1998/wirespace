# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
import os

# Create your views here.
def home(request):
	if not request.method=="POST":
		current_path="./"
		curr_dir_items=os.listdir(current_path)
		curr_dir={}
		for item in curr_dir_items:
			if(os.path.isdir(item)):
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
		curr_dir_items=os.listdir(current_path)
		if curr_dir_items:
			curr_dir={}
			for item in curr_dir_items:
				if(os.path.isdir(os.path.join(current_path,item))):
					curr_dir[item]="dir"
				else:
					curr_dir[item]="file"

			context={'list':curr_dir,'current_path':current_path}
			return render(request,'Server/index.html',context)
		else:
			return HttpResponse("This directory is empty")
		
			