from django.db import models
import binascii
import os
import datetime

# Create your models here.
def gen_key(length=16):
	new_key=binascii.hexlify(os.urandom(length))
	while Key.objects.filter(key=new_key).count()>0:
		new_key=binascii.hexlify(os.urandom(length))
	return new_key

class Key(models.Model):
	key=models.CharField(max_length=32,default=gen_key,editable=False,	primary_key=True,help_text="This value is temporary. Use the final value after saving.")
	permission=models.CharField(max_length=1,choices=(('r','Read-only'),('w','Read-and-Write')),default='r')
	shared_to=models.CharField(max_length=30,default="Anonymous")
	email=models.EmailField(max_length=254,help_text="E-mail of the person with whom the space is shared")
	space_allotted=models.BigIntegerField(help_text="Space you want to share in BYTES")
	path_shared=models.TextField(default="/home/yash/Public",max_length=100)
	created_on=models.DateTimeField(auto_now_add=True)
	expires_on=models.DateTimeField(default=None)

	def __str__(self):
		return self.shared_to+" -> "+self.path_shared

	def time_slot(self):
		return "{:%d %b %Y, %X}".format(self.created_on)+" --- "+"{:%d %b %Y, %X}".format(self.expires_on)

	def space_shared(self):
		suffix='B'
		num=self.space_allotted
		for unit in ['','K','M','G','T']:
			if abs(num)<1024.0:
				return "%3.2f%s%s"%(num, " "+unit, suffix)
			num /= 1024.0
		return "%3.2f%s%s"%(num,'P', suffix)

	def link(self):
		ip='10.42.0.3' # Obtain IP and initialize it here
		port='8000' # Obtain the port and initialize it here
		return ip+":"+port+"/share/"+self.key

	def save(self,*args,**kwargs):
		if self.expires_on==None:
			self.expires_on=self.created_on+datetime.timedelta(weeks=1)
		super().save(*args,**kwargs)
