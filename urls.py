#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from django.conf.urls.defaults import *
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        (r'^', include('apps.core.urls')),
)

urlpatterns += patterns('',
)

  