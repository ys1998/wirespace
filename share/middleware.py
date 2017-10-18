# Middleware to authenticate token and expire keys
from django.http import HttpResponse,JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import *
import re

CHECK_LIST = [
	'/share/',
	'/share/open/',
	'/share/upload/',
	'/share/download/',
	'/share/delete/',
	'/share/create_folder/',
	'/share/search/',
]

POST_IGNORE_LIST = [
	'/share/',
]

re_host=re.compile('/host/.*')
re_key=re.compile('/[0-9a-f]{16}/$')

class AuthenticateTokenMiddleware(MiddlewareMixin):
	def process_request(self,request):
		global CHECK_LIST
		if request.get_full_path() in CHECK_LIST:
			if request.method == "POST":
				if 'token' not in request.session:
					return JsonResponse({'status':'false','message':"Unauthorized access detected."}, status=403)
				elif Token.objects.filter(token=request.session['token']).count()==0:
					return JsonResponse({'status':'false','message':"Token is unidentifiable."}, status=404)
				else:
					print("Valid request.")
					return None
			else:
				if request.get_full_path() in POST_IGNORE_LIST:
					print("Valid request.")
					return None
				else:
					return JsonResponse({'status':'false','message':"Invalid request format."}, status=404)
		else:
			path=request.get_full_path()
			if re_host.match(path) is None and re_key.match(path) is None:
				return JsonResponse({'status':'false','message':"Invalid request to {0}.".format(request.get_full_path())}, status=404)
			else:
				return None
			