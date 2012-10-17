from serwis.zpi import views
from django.conf.urls import patterns, include, url
import os.path

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', views.glowna),
    #(r'^$', views.rejestruj),
    (r'^x$', views.wygenerujAktywator),
    (r'^logIn$', views.logowanie),
    (r'^checkUsername/(.*)$', views.sprawdzNick),
    (r'^checkIndexNumber/(.*)$', views.sprawdzIndeks),
    (r'^sendEmail$', views.wyslijEmail),
    (r'^registration$', views.rejestruj),
    (r'^register$', views.zarejestruj),
    (r'^rememberPassword$', views.przypomnijHaslo),
    (r'^confirm/(.*)/(\d{6})$', views.potwierdzRejestracje),
    
    # MEDIA
    (r'^media/html/portal.html$', views.zaladujPortal),     
    (r'^media/html/timetable.html$', views.zaladujPlan),
    (r'^media/html/calendar.htmll$', views.zaladujKalendarz),
    (r'^media/html/teachers.htmll$', views.zaladujWykladowcow), 
    (r'^media/html/map.html$', views.zaladujMape),
    
    (r'^css/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/css')}),
    (r'^img/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/img')}),
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
)
