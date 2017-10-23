from django.db import models
from django.utils import timezone as dj_tz
from django.core.validators import ValidationError
import binascii
import os,subprocess
import datetime
from django.conf import settings

# Create your models here.
def gen_key(length=8):
	new_key=binascii.hexlify(os.urandom(length))
	while Key.objects.filter(key=new_key).count()>0:
		new_key=binascii.hexlify(os.urandom(length))
	return new_key.decode('utf-8')

class Key(models.Model):
	key=models.CharField(max_length=8,default=gen_key,editable=False,	primary_key=True,help_text="This value is temporary. Use the final value after saving.")
	permission=models.CharField(max_length=1,choices=(('r','Read-only'),('w','Read-and-Write')),default='r')
	shared_to=models.CharField(max_length=30,default="Anonymous")
	email=models.EmailField(max_length=254,help_text="E-mail of the person with whom the space is shared",null=True,blank=True)
	space_allotted=models.BigIntegerField(help_text="Space to be shared, in BYTES",default=4096)
	path_shared=models.TextField(default=os.path.expanduser("~/Desktop"),max_length=100)
	created_on=models.DateTimeField(auto_now_add=True)
	expires_on=models.DateTimeField(default=None)

	def __str__(self):
		return self.shared_to+" -> "+self.path_shared

	def time_slot(self):
		return "{:%d %b %Y, %I:%M:%S %p}".format(dj_tz.localtime(self.created_on))+" --- "+"{:%d %b %Y, %I:%M:%S %p}".format(dj_tz.localtime(self.expires_on))

	def space_available(self):
		suffix='B'
		try:
			current_space=int(subprocess.check_output(["du","-s",self.path_shared]).split()[0])
		except:
			current_space=-1
		# current_space=10240
		num=max(0,self.space_allotted-current_space)
		for unit in ['','K','M','G','T']:
			if abs(num)<1024.0:
				return "%3.2f%s%s"%(num, " "+unit, suffix)
			num /= 1024.0
		return "%3.2f%s%s"%(num,'P', suffix)

	# Link generating function
	def link(self):
		ip=str(settings.HOST_IP) # Obtain IP from settings.py
		port=str(settings.PORT) # Obtain the port from settings.py
		return ip+":"+port+"/"+self.key

	# Form validation function
	def clean(self):
		if dj_tz.localtime(self.expires_on)<=dj_tz.localtime(self.created_on):
			raise ValidationError("expires_on : Expiration time must come after creation time.")

		if not os.path.isdir(self.path_shared):
			raise ValidationError("path_shared : Enter a valid directory for sharing.")

	# Save function with some modifications
	def save(self,*args,**kwargs):
		if self.expires_on==None:
			self.expires_on=self.created_on+datetime.timedelta(weeks=1)
		if self.path_shared.strip()=="":
			self.path_shared=os.path.expanduser('~')
		else:
			self.path_shared=self.path_shared.strip()

		if Key.objects.filter(key=self.key).count()==0 or Key.objects.get(key=self.key).path_shared!=self.path_shared:
			if Key.objects.filter(key=self.key).count()==0:
				# Convert space shared to TOTAL space shared - i.e. account for already consumed space
				dir_space=int(subprocess.check_output(["du","-b","--max-depth=0",self.path_shared]).split()[0])
				self.space_allotted+=dir_space
			else:
				new_dir_space=int(subprocess.check_output(["du","-b","--max-depth=0",self.path_shared]).split()[0])
				old_dir_space=int(subprocess.check_output(["du","-b","--max-depth=0",Key.objects.get(key=self.key).path_shared]).split()[0])
				self.space_allotted+=new_dir_space-old_dir_space

		super().save(*args,**kwargs)

# hidden model to maintain tokens
def gen_token(length=16):
	new_token=binascii.hexlify(os.urandom(16))
	while Token.objects.filter(token=new_token).count()>0:
		new_token=binascii.hexlify(os.urandom(16))
	return new_token.decode('utf-8')

class Token(models.Model):
	link=models.ForeignKey(Key,on_delete=models.CASCADE,default=None)
	token=models.CharField(max_length=16,default=gen_token,editable=False,primary_key=True)
	IP=models.CharField(max_length=15,default=None)

	def __str__(self):
		return self.token

	def save(self,*args,**kwargs):
		if not self.link:
			return
		if not self.token:
			new_token=binascii.hexlify(os.urandom(16))
			while Token.objects.filter(token=new_token).count()>0:
				new_token=binascii.hexlify(os.urandom(16))
			self.token=new_token
		if not self.IP:
			self.IP=''
		super().save(*args,**kwargs)