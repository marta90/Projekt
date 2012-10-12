from serwis.zpi import views
from django.conf.urls import patterns, include, url
import os.path

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', views.glowna),
    (r'^logIn$', views.logowanie),
    (r'^checkUsername/(.*)$', views.sprawdzNick),
    (r'^checkIndexNumber/(.*)$', views.sprawdzIndeks),
	
	
    # Examples:
    # url(r'^$', 'serwis.views.home', name='home'),
    # url(r'^serwis/', include('serwis.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
)
