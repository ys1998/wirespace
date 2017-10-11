from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Key,Token

# Register your models here.

class KeyAdmin(admin.ModelAdmin):
    readonly_fields=('key','created_on')
    fields=['key','created_on','expires_on','path_shared','permission','space_allotted','shared_to','email']
    list_display=('link','shared_to','path_shared','time_slot','space_shared','permission')
    formfield_overrides = {
    	models.TextField: {
    		'widget': Textarea(
    			attrs={'rows': 1,
    				   'cols': 50,
    				   # 'style': 'height: 1em;'
    				  })}}

    
admin.site.register(Key,KeyAdmin)
admin.site.register(Token)