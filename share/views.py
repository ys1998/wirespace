from django.shortcuts import render
import os
from django.http import HttpResponse
import django.utils 

# Create your views here.
def directory(request,addr='/'):
    
    if not addr or addr[0]!='/':
        prefix = os.path.expanduser('~')+'/'
    else:
        prefix =''
    if not addr or addr[-1]!='/':
        addr += '/'
    file_list = [prefix + addr + x for x in os.listdir(prefix+addr)]
    dir_or_file={}
    for files in file_list:
        if(os.path.isdir(files)):
            dir_or_file[files]='dir'
        else:
            dir_or_file[files]='file'
        #else:
         #   dir_or_files[files]='hidden'
    
    context={'file_list':dir_or_file, 'original_directory':prefix+addr}
    return render(request,'share/directory.html',context)
