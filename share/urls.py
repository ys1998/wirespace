## @package urls
#
# This package contains the description and resolution of all urls required for the project.
from django.conf.urls import url
from . import views

## List that contains matching regex for urls and corresponding view functions to be invoked
urlpatterns=[
	url(r'^$',views.home,name='home'),
        url(r'^open/$',views.open_item,name='open'),
        url(r'^download/$',views.download_item,name='download'),
        url(r'^search/$',views.search,name='search'),
        url(r'^upload/$',views.upload,name='upload'),
        url(r'^create_folder/$',views.create_folder,name='create_folder'),
        url(r'^delete/$',views.delete,name='delete'),
        url(r'^move/$',views.move,name='move'),
        #url(r'^admin/$',views.home,name='home'),
]
