from django.conf.urls import url
from . import views

urlpatterns=[
        url(r'^$',views.home,name='home'),
        url(r'^open/$',views.open_item,name='open'),
        url(r'^download/$',views.download_item,name='download'),
        url(r'^search/$',views.search,name='search'),
        url(r'^upload/$',views.upload,name='upload'),
        #url(r'^admin/$',views.home,name='home'),
]
