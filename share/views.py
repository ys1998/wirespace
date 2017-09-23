from django.shortcuts import render
import os

def directory(request, addr):
    if not addr or addr[0] != '/':
        home = os.path.expanduser('~') + '/' 
    else:
        home = ''

    directory_list = [x + os.path.expanduser('/') for x in os.listdir(home + addr)]
    return render(request, 'share/directory.html', {
            'directory' : home + addr,
            'directory_list' : directory_list
            })

# Create your views here.
