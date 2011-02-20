#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('apps.core.views',
        url(r'^$', 'index', name="index"),
        url(r'^login/$', 'login', {'template_name': 'registration/login.haml'}, name="login"),
 )

urlpatterns += patterns('',
        url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name="logout"),
)
