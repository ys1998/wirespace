import sys, socket, subprocess

action=sys.argv[1]
if action=="get_ip":
	s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8",8000))
	print(s.getsockname()[0])
	s.close()

elif action=="configure":
	ip=str(sys.argv[2])
	port=str(sys.argv[3])
	debug=str(sys.argv[4])

	subprocess.call(["sed","-i","s/^ALLOWED_HOSTS.*$/ALLOWED_HOSTS = \['"+ip+"'\]/g", "wirespace/settings.py"])
	subprocess.call(["sed","-i","s/^PORT.*$/PORT = "+port+"/g", "wirespace/settings.py"])
	subprocess.call(["sed","-i","s/^HOST_IP.*$/HOST_IP = '"+ip+"'/g", "wirespace/settings.py"])
	subprocess.call(["sed","-i","s/^DEBUG.*$/DEBUG = "+debug+"/g", "wirespace/settings.py"])