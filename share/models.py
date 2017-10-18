from django.db import models
from django.utils import timezone as dj_tz
import binascii
import os
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
	space_allotted=models.BigIntegerField(help_text="Space you want to share in BYTES",default=4096)
	path_shared=models.TextField(default=os.path.expanduser("~"),max_length=100)
	created_on=models.DateTimeField(default=dj_tz.now(),editable=False)
	expires_on=models.DateTimeField(default=None)

	def __str__(self):
		return self.shared_to+" -> "+self.path_shared

	def time_slot(self):
		return "{:%d %b %Y, %I:%M:%S %p}".format(dj_tz.localtime(self.created_on))+" --- "+"{:%d %b %Y, %I:%M:%S %p}".format(dj_tz.localtime(self.expires_on))

	def space_shared(self):
		suffix='B'
		num=self.space_allotted
		for unit in ['','K','M','G','T']:
			if abs(num)<1024.0:
				return "%3.2f%s%s"%(num, " "+unit, suffix)
			num /= 1024.0
		return "%3.2f%s%s"%(num,'P', suffix)

	def link(self):
		ip=str(settings.HOST_IP) # Obtain IP and initialize it here
		port=str(settings.PORT) # Obtain the port and initialize it here
		return ip+":"+port+"/"+self.key

	def save(self,*args,**kwargs):
		self.created_on=dj_tz.now()
		if self.expires_on==None:
			self.expires_on=self.created_on+datetime.timedelta(weeks=1)
		if self.path_shared.strip()=="":
			self.path_shared="/"
		else:
			self.path_shared=self.path_shared.strip()

		print(self.created_on)
		print(self.expires_on)
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
	ip=models.CharField(max_length=15,default=None)

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
		if not self.ip:
			self.ip=''
		super().save(*args,**kwargs)