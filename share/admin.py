from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Key,Token

# Register your models here.

class KeyAdmin(admin.ModelAdmin):
    # readonly_fields=('key','created_on')
    fields=['key','created_on','expires_on','path_shared','permission','space_allotted','shared_to','email']
    list_display=('link','shared_to','path_shared','time_slot','space_available','permission')
    formfield_overrides = {
    	models.TextField: {
    		'widget': Textarea(
    			attrs={'rows': 1,
    				   'cols': 50,
    				})}}
    
    # Overriden method
    # Alter fields once object has been created and saved
    def get_readonly_fields(self,request,obj=None):
        if obj:
            # Change help_text and readonly_fields once object has been saved
            obj._meta.get_field('space_allotted').help_text="Total space shared in BYTES (including existing space)"
            return ('key','created_on','space_allotted')
        else:
            return ('key','created_on')

    
admin.site.register(Key,KeyAdmin)
# admin.site.register(Token)