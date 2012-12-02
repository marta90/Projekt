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
    (r'^lostPassword$', views.przypomnijHaslo),                 
    (r'^newPassword/(.*)/(.*)$', views.ustawNoweHaslo),        
    (r'^repeatVerification$', views.przeslijAktywatorPonownie), 
    (r'^changePassword$', views.zapiszNoweHaslo),               
    (r'^changePasswordAccount$', views.zmienHaslo),             
    (r'^confirm/(.*)/(.*)$', views.potwierdzRejestracje),       #potwierdzenie rejestracji poprzez link aktywacyjny
    (r'^remove/(.*)/(.*)$', views.anulujRejestracje),           #anulowanie rejestracji poprzez link aktywacyjny
    (r'^generujPlan$', include('pwrParser.urls')),              #widok wczytujacy kod z Edu i generujacy plan.
    (r'^addStudent$', views.dodajKierunek),
    (r'^changeDefaultStudent$', views.zmienDomyslnegoSt),
    (r'^removeStudent$', views.usunStudenta),
    
    (r'^giveLessons/(.*)/(.*)$', views.pobierzZajecia),
    (r'^addEvent$', views.dodajWydarzenie),
    (r'^sendEmailAccount$', views.wyslijEmailZProsba),
    (r'^shout/(.*)$', views.dodajShout),
    (r'^getTeachers/(.)$', views.wykladowcaNaLitere),
    (r'^getTutorial/(.*)$', views.konsultacjeWykladowcy),
    (r'^findTeacher/(.*)$', views.znajdzWykladowce),
    (r'^changeAccountSettings$', views.edytujDane),
    (r'^addEventToCalendar/(.*)$', views.dodajWydDoKalendarza),
    (r'^getTeachersLessons/(.*)/(.*)/(.*)$', views.pobierzZajeciaWykladowcy),
    (r'^editEventDescription$', views.zmienOpis),
    
    #PLAN POBIERANIE I ZAPISYWANIE NOTATEK
    (r'^getNotes/(.*)/(.*)$', views.getNotes),
    (r'^saveNotes$', views.saveNotes),
    
    #ANDROID
    (r'^test$', views.test),                                                        #klasa do testow
    (r'^getEventsAndroid$', views.mojeWydarzeniaAND),                               #przeslanie do And. zblizajacych sie wydarzen
    (r'^getLastEventsAndroid$', views.ostatnieWydarzeniaAND),                       #przeslanie do And. ostatnio dodanych wydarzen
    (r'^getTeachersAndroid$', views.listaWykladowcowAND),                           #przeslanie do And. listy wykladowcow
    (r'^shoutAndroid$', views.dodajWShoutboxieAND),
    (r'^logInAndroid$', views.logowanieAND),
    (r'^accountAndroid$', views.daneStudentaAND),
    (r'^addEventToCalendarAndroid$', views.dodajWydDoKalendarzaAND),
    (r'^getShoutboxAndroid$', views.shoutboxAND),
    (r'^getCalendarAndroid$', views.kalendarzAND),
    (r'^getTimetableAndroid$', views.planAND),
    (r'^changePswdLoginAndroid$', views.zmianaHaslaPrzyLogowaniuAND),
    (r'^sendActivatorAndroid$', views.przeslijAktywatorPonownieAND),
    (r'^qrCodeAndroid$', views.dodajZQrAND),
    (r'^qrAndroid/(.*)$', views.qrAND),
    (r'^addEventAndroid$', views.dodajWydarzenieAND),
    (r'^switchSpec/(.*)$', views.zamienStudenta),
    (r'^mapAndroid$', views.mapaAND),
    
    # MEDIA
    (r'^media/html/portal.html$', views.zaladujPortal),
    (r'^media/html/news.html$', views.zaladujNewsy),
    (r'^media/html/shoutbox.html$', views.zaladujShoutbox),
    (r'^media/html/timetable2.html$', views.zaladujPlan),
    (r'^media/html/calendar.html$', views.zaladujKalendarz),
    (r'^media/html/teachers.html$', views.zaladujWykladowcow), 
    (r'^media/html/map.html$', views.zaladujMape),
    (r'^media/html/account.html$', views.zaladujKonto),
    (r'^media/html/registration.html$', views.zaladujRejestracje),
    (r'^media/html/changePassword.html$', views.zaladujZmianeHasla),
    
    
    (r'^css/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/css')}),
    (r'^img/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media/html/img')}),
    (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(os.path.dirname(__file__), 'media')}),
)
