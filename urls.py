#coding=utf-8
#--- Author: Dmitri Patrakov <traditio@gmail.com>
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

from staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()


urlpatterns = patterns('',
        (r'^$', 'coffin.views.generic.simple.direct_to_template', {'template': 'base.haml'}),
        (r'^sentry/', include('sentry.urls')),
        (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
