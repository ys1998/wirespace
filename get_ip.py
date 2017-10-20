import socket
s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8",8000))
print(s.getsockname()[0])
s.close()
