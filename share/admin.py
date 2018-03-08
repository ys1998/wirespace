## @file admin.py
#
# This file defines how the admin page should look like.

from django.contrib import admin
from django.db import models
from django.forms import Textarea
from .models import Key,Token

## @brief Class that handles how the Key section would look on the admin page
class KeyAdmin(admin.ModelAdmin):
    ## The fields to be included
    fields=['key','expires_on','path_shared','permission','space_allotted','shared_to','email']
    ## The fields to be displayed as columns in the tabular form
    list_display=('link','shared_to','path_shared','time_slot','space_available','permission')
    ## Defines overriding widgets for specified fields
    formfield_overrides = {
    	models.TextField: {
    		'widget': Textarea(
    			attrs={'rows': 1,
    				   'cols': 50,
    				})}}
    
    ## @brief Overridden function to specify which fields are read-only
    #
    # It converts the 'space_allotted' field to a read-only field once the Key object has been created.
    # @param self A KeyAdmin instance
    # @param request An HttpRequest containing required metadata
    # @param obj The Key object associated with the request
    # @returns A list of read-only fields depending on the context
    def get_readonly_fields(self,request,obj=None):
        if obj:
            # Change help_text and readonly_fields once object has been saved
            obj._meta.get_field('space_allotted').help_text="Total space shared in BYTES (including existing space)"
            return ('created_on','space_allotted')
            return ('created_on','space_allotted')
        else:
            return ('created_on')
            return ('created_on')

## @brief Class that handles how the Token section would look on the admin page
class TokenAdmin(admin.ModelAdmin):
    ## List of all read-only fields
    readonly_fields=('link','token','IP')
    ## List of all fields to be included
    fields=['link','token','IP']
    ## List of fields to be displayed as columns in the tabular form
    list_display=('token','link')   
    
    
admin.site.register(Key, KeyAdmin)
admin.site.register(Token, TokenAdmin)