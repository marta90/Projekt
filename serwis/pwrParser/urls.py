from serwis.zpi import views
from django.conf.urls import patterns, include, url
import os.path

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'pwrParser.views.generujPlan'),
    
    (r'^css/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/css')}),
    (r'^img/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/img')}),
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
)
