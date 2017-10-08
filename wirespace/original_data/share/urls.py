from django.conf.urls import url
from . import views

urlpatterns=[
        url(r'^$',views.home,name='home'),
        #url(r'^admin/$',views.home,name='home'),
]
