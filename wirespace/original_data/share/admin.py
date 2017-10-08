from django.contrib import admin
from .models import Key

# Register your models here.

class KeyAdmin(admin.ModelAdmin):
    readonly_fields=('key','created_on')
    fields=['key','created_on','expires_on','permission','shared_to','email','path_shared','space_allotted']
    list_display=('key','shared_to','path_shared','time_slot','space_shared','permission')

    
admin.site.register(Key,KeyAdmin)