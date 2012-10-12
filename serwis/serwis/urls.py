from django.conf.urls import patterns, include, url
import os.path


# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^serwis/$', 'serwis.zpi.views.glowna'),
    url(r'^logowanie$', 'serwis.zpi.views.logowanie'),
    # Examples:
    # url(r'^$', 'serwis.views.home', name='home'),
    # url(r'^serwis/', include('serwis.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    
    (r'^static2/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'static2')}),
)
