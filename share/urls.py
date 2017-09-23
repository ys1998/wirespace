from django.conf.urls import url
from . import views

app_name = 'share'
urlpatterns = [
    url(r'^(?P<addr>.*)/$', views.directory, name = 'addr') #parse as complete address in the url 
]
