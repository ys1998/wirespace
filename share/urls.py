from django.conf.urls import url
from . import views

urlpatterns=[
		url(r'^$',views.home,name='home'),
        url(r'^open/$',views.open_item,name='open'),
        url(r'^download/$',views.download_item,name='download'),
        url(r'^search/$',views.search,name='search'),
        url(r'^upload/$',views.upload,name='upload'),
        url(r'^create_folder/$',views.create_folder,name='create_folder'),
        url(r'^delete/$',views.delete,name='delete'),
        #url(r'^admin/$',views.home,name='home'),
]
