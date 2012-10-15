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
    
    # MEDIA
    (r'^media/html/portal.html$', views.zaladujPortal),     
    (r'^media/html/timetable.html$', views.zaladujPlan),
    (r'^media/html/calendar.htmll$', views.zaladujKalendarz),
    (r'^media/html/teachers.htmll$', views.zaladujWykladowcow), 
    (r'^media/html/map.html$', views.zaladujMape),
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
)
