from serwis.zpi import views
from django.conf.urls import patterns, include, url
import os.path

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', views.glowna),                                      #widok strony glownej
    (r'^/$', views.glowna),                                     #widok strony glownej
    (r'^logIn$', views.logowanie),                              #widok obslugujacy logowanie
    (r'^logOut$', views.wylogowanie),                           #widok obslugujacy wylogowywanie
    (r'^checkUsername/(.*)$', views.sprawdzNick),               #zapytanie do serwera czy dany login jest juz w systemie
    (r'^checkIndexNumber/(.*)$', views.sprawdzIndeks),          #zapytanie do serwera czy dany indeks jest juz w systemie
    (r'^giveSpecialization/(.*)$', views.pobierzKierunki),      #zapytanie do serwera o kierunki jakie sa na danym wydziale
    (r'^giveSemester/(.*)/(.*)$', views.pobierzSemestry),       #zapytanie do serwera o semestry jakie sa na danym kierunku i rodzaju studiow
    (r'^sendEmail$', views.wyslijEmail),                        #widok obslugujacy wysylanie maila do admina
    (r'^registration$', views.rejestruj),                       #widok obslugujacy przejscie do strony "registration.html"
    (r'^register$', views.zarejestruj),                         #widok obslugujacy transakcje rejestrowania
    (r'^rememberPassword$', views.przypomnijHaslo),             
    (r'^confirm/(.*)/(\d{6})$', views.potwierdzRejestracje),    #potwierdzenie rejestracji poprzez link aktywacyjny
    (r'^generujPlan$', include('pwrParser.urls')),              #widok wczytujacy kod z Edu i generujacy plan.
    
    #ANDROID
    (r'^test$', views.test),                                    #klasa do testow
    (r'^getEventsAndroid$', views.mojeWydarzeniaAND),           #przeslanie do And. zblizajacych sie wydarzen
    (r'^getLastEventsAndroid$', views.ostatnieWydarzeniaAND),   #przeslanie do And. ostatnio dodanych wydarzen
    (r'^shout$', views.dodajWShoutboxieAND),                    #zapisanie wiadomosci z And. w bazie - Jeszcze nie obslugiwane
    
    # MEDIA
    (r'^media/html/portal.html$', views.zaladujPortal),     
    (r'^media/html/timetable.html$', views.zaladujPlan),
    (r'^media/html/calendar.html$', views.zaladujKalendarz),
    (r'^media/html/teachers.html$', views.zaladujWykladowcow), 
    (r'^media/html/map.html$', views.zaladujMape),
    (r'^media/html/account.html$', views.zaladujKonto),
    
    (r'^css/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/css')}),
    (r'^img/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/img')}),
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
)
