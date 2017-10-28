## @package models
#
# This package contains the description of the Key and Token classes, which are used for authentication purposes in the project.

from django.db import models
from django.utils import timezone as dj_tz
from django.core.validators import ValidationError
import binascii
import os,subprocess
import datetime
from django.conf import settings

##	@brief Function to generate a random hex-string of given length.
#	This function keeps on generating a new string until it finds one that does not exist in the database.
#	@param length The length of the hexstring to be generated with default as 8
#	@returns A random, unique, hex-string of specified length
def gen_key(length=8):
	new_key=binascii.hexlify(os.urandom(length))
	while Key.objects.filter(key=new_key).count()>0:
		new_key=binascii.hexlify(os.urandom(length))
	return new_key.decode('utf-8')

## @brief Class to store all the information about the shared space.
# It saves these details to the database and helps in their retrieval upon clients' requests.
class Key(models.Model):
	## Stores the unique key associated with each instance that is provided to the client
	key=models.CharField(max_length=8,default=gen_key,editable=False,	primary_key=True,help_text="This value is temporary. Use the final value after saving.")
	## The permission that the host gives to the client. Can be one of 'read' or 'read-and-write'
	permission=models.CharField(max_length=1,choices=(('r','Read-only'),('w','Read-and-Write')),default='r')
	## Name of the client to which the Key is shared
	shared_to=models.CharField(max_length=30,default="Anonymous")
	## An optional field to store the email address of the client for sending notifications
	email=models.EmailField(max_length=254,help_text="E-mail of the person with whom the space is shared",null=True,blank=True)
	## The additional space provided by the host to the client apart from the already existing space in the specified \a path_shared
	space_allotted=models.BigIntegerField(help_text="Space to be shared, in BYTES",default=4096)
	## The shared path/directory associated with this instance
	path_shared=models.TextField(default=os.path.expanduser("~/Desktop"),max_length=100)
	## The timestamp when this instance was created. Gets filled automatically during time of creation and cannot be altered.
	created_on=models.DateTimeField(auto_now_add=True)
	## The date and time upto which the host wants to share his space
	expires_on=models.DateTimeField(default=None)

	## Function to generate the string representation of an instance
	# @param self An instance of Key class that needs to be represented
	# @returns A string representation of \a self
	def __str__(self):
		return self.shared_to+" -> "+self.path_shared

	## @brief Function to generate a string representation of the time interval within which the key is active
	# @param self An instance of Key class
	# @returns A string representation of the time-interval for the specified instance
	def time_slot(self):
		return "{:%d %b %Y, %I:%M:%S %p}".format(dj_tz.localtime(self.created_on))+" --- "+"{:%d %b %Y, %I:%M:%S %p}".format(dj_tz.localtime(self.expires_on))

	## @brief Function to display the space avaiable for use
	# @param self An instance of Key class
	# @returns String representation of the space available for usage by the client in human-readable form
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

	## @brief Function to generate the shareable link.
	# It concatenates the unique key associated with the instance with the host's IP.
	# @param self An instance of Key class
	# @returns The shareable link to be shared with the client
	def link(self):
		ip=str(settings.HOST_IP) # Obtain IP from settings.py
		port=str(settings.PORT) # Obtain the port from settings.py
		return ip+":"+port+"/"+self.key

	## @brief Function to validate the Key instance before it is saved
	# It raises a ValidationError if some error in the to-be-created instance is detected
	# @param self An instance of Key class
	def clean(self):
		if dj_tz.localtime(self.expires_on)<=dj_tz.localtime(self.created_on):
			raise ValidationError("expires_on : Expiration time must come after creation time.")

		if not os.path.isdir(self.path_shared):
			raise ValidationError("path_shared : Enter a valid directory for sharing.")

	## @brief Function that overrides the default save function
	# It fills optional, blank fields with default values before the instance is saved. It also adds the current space occupied by the \a path_shared directory to the \a space_allotted variable to account for the total space shared.
	# @param self The instance of Key class
	# @param *args Non-keyworded argument list
	# @param **kwargs Keyworded argument list
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

## @brief Function to generate a unique token of specifed length
# @param length The length of the token to be generated with default as 16
# @returns A string representing the unique, hexadecimal token generated
def gen_token(length=16):
	new_token=binascii.hexlify(os.urandom(16))
	while Token.objects.filter(token=new_token).count()>0:
		new_token=binascii.hexlify(os.urandom(16))
	return new_token.decode('utf-8')

## @brief Class representing tokens for one-time-authentication using key
# Client data such as the associated key and IP address is stored in its instances.
class Token(models.Model):
	## Stores the Key instance associated with it
	link=models.ForeignKey(Key,on_delete=models.CASCADE,default=None)
	## The unique, auto-generated token assigned to a client on providing a valid key
	token=models.CharField(max_length=16,default=gen_token,editable=False,primary_key=True)
	## Stores the IP address of the client, if detected, for future reference
	IP=models.CharField(max_length=15,default=None)

	## @brief Function to generate string representation of a Token instance
	# @param self A Token instance
	# @returns The \a token attribute of the instance as a string
	def __str__(self):
		return self.token

	## @brief Function that overrides the default save function
	# It first validates the fields, not saving the instance if any error is found. On successful validation, it saves the instance by calling the super save() function
	# @param self A Token instance
	# @param *args Non-keyworded arguments
	# @param **kwargs Keyworded arguments
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