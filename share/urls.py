from django.conf.urls import url
from . import views

urlpatterns = [
        url(r'^(?P<addr>.*)/$',views.directory,name='addr'),
        url(r'^$',views.directory,name='addr'),
        ]
