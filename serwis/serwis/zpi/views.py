from django.shortcuts import render_to_response
from serwis.zpi import models
from django.http import HttpResponse, HttpResponseRedirect
from passlib.hash import sha256_crypt
from django.core.mail import send_mail
from django.db import transaction
from django.core import serializers
import time, datetime
import os
import string
import random
import re
import json
import urllib
import urllib2
from collections import defaultdict
from twill import commands
from django.db.models import Q

from django.utils import simplejson
from serwis.zpi.mainFunctions import *


from serwis.zpi.android import *
from serwis.zpi.portal import *
from serwis.zpi.timetable import *
from serwis.zpi.teachers import *
from serwis.zpi.calendar import *
from serwis.zpi.account import *
from serwis.zpi.news import *
from serwis.zpi.map import *


adresSerwera = "127.0.0.1:8000"

############### STRONA GLOWNA #############################################################

# Wyswietlenie strony glownej
def glowna(request):
	# Uzytkownik jest zalogowany
	if jestSesja(request):
		nick = uzSesja(request).nick
		if 'content' not in request.session.keys():
			request.session['content'] = 'news'
		
		# Uzytkownik logowal sie - trzeba odpowiednio ustawić ciastko
		if 'login' in request.session.keys():
			log = request.session['login']
			
			# Opcja "zapamietaj" nie byla zaznaczona = usuwamy ciastko
			if log == "":
				response = render_to_response('index.html', {'strona':request.session['content'], 'nick':nick, 'wyloguj':"wyloguj"})
				try:
					response.delete_cookie('login')
				except:
					pass
				del request.session['login']
				return response
			
			# Opcja "zapamietaj" byla zaznaczona = dodajemy ciastko z loginem
			else:
				response = render_to_response('index.html', {'strona':request.session['content'], 'nick':nick, 'wyloguj':"wyloguj"})
				response.set_cookie('login', log)
				del request.session['login']
				return response
		
		# Uzytkownik przemieszcza sie po serwisie
		else:
			return render_to_response('index.html', {'strona':request.session['content'], 'nick':nick, 'wyloguj':"wyloguj"})
	
	# Uzytkownik nie jest zalogowany oraz wystapil blad podczas logowania lub rejestracji
	elif 'komunikat' in request.session:
		kom = request.session['komunikat']
		
		#################################
		# Logowanie
		# Blad wyslania
		if kom == '1':
			usunSesje(request)
			tekst = "Wystąpił błąd. Spróbuj ponownie."
			return render_to_response('index.html', {'strona':'portal', 'logowanie':True, 'blad':True, 'tekstBledu':tekst})
		
		# Błędny login lub hasło
		elif kom == '2':
			usunSesje(request)
			tekst = 'Podany login i/lub hasło są nieprawidłowe.'
			return render_to_response('index.html', {'strona':'portal', 'logowanie':True, 'blad':True, 'tekstBledu':tekst})
		
		# Konto nieaktywne
		elif kom == '3':
			usunSesje(request)
			tekst = 'Musisz aktywować konto, aby móc się zalogować. Jeśli chcesz wysłać aktywator jeszcze raz kliknij w poniższy link.'
			return render_to_response('index.html', {'strona':'portal', 'logowanie':True, 'blad':True, 'tekstBledu':tekst, 'wyslijAktywator':True})
		
		# Wymagana zmiana hasla
		elif kom == '4':
			del request.session['komunikat']
			tekst = 'Teraz możesz zmienić swoje hasło.'
			return render_to_response('index.html', {'strona':'portal', 'logowanie':True, 'blad':True, 'tekstBledu':tekst, 'zmianaHasla':True})
		
		##################################
		# Rejestracja
		# Wyswietlenie rejestracji
		elif kom == '5':
			#usunSesje(request)
			return render_to_response('index.html', {'strona':'registration', 'logowanie':True})
	
	# Uzytkownik nie jest zalogowany
	else:
		if 'content' not in request.session.keys():
			request.session['content'] = 'portal'
		if 'login' in request.COOKIES.keys():
			return render_to_response('index.html', {'strona':request.session['content'], 'logowanie':True, 'jestLogin':True, 'login':request.COOKIES['login']})
		else:
			return render_to_response('index.html', {'strona':request.session['content'], 'logowanie':True})



############### REJESTRACJA ##############################################################

# Zaladowanie rejestracji
def zaladujRejestracje(request):
	nick = request.session['fld_loginCheck']
	indeks = request.session['fld_indexNumber']
	wydz = models.Wydzial.objects.all()
	usunSesje(request)
	return render_to_response('registration.html', {'nick': nick, 'index': indeks, 'wydzialy': wydz})


# Wyswietlenie rejestracji
def rejestruj(request):
	if post(request):
		request.session['fld_loginCheck'] = request.POST['fld_loginCheck']
		request.session['fld_indexNumber'] = request.POST['fld_indexNumber']
		request.session['komunikat'] = '5'
		return HttpResponseRedirect('/')
	else:
		return HttpResponse("Nie sprawdzono poprawności loginu oraz numer indeksu.") #<------------------------- oprogramować wyświetlanie tego!!!!


# Pobieranie kierunków - używane przy ajaxie
def pobierzKierunki(request, idWydzialu):
	kierunki = models.Kierunek.objects.filter(wydzial__id = idWydzialu)
	odp = ""
	for k in kierunki:
		odp = odp + 'obj.options[obj.options.length] = new Option(\''+ k.nazwa +'\' , \'' + str(k.id) + '\'); '
	return HttpResponse(odp)


# Pobieranie semestrów - używane przy ajaxie
def pobierzSemestry(request, idSpec, idTyp):
	kierunek = models.Kierunek.objects.get(id = idSpec)
	odp = ""
	if idTyp == "1":
		for i in range(1, kierunek.liczbaSemestrow1st + 1):
			odp = odp + 'obj.options[obj.options.length] = new Option(\''+ str(i) +'\' , \'' + str(i) + '\'); '
	if idTyp == "2":
		for i in range(1, kierunek.liczbaSemestrow2stPoInz + 1):
			odp = odp + 'obj.options[obj.options.length] = new Option(\''+ str(i) +'\' , \'' + str(i) + '\'); '
	return HttpResponse(odp)



# Rejestracja użytkownika
@transaction.commit_on_success
def zarejestruj(request):
	usunSesje(request)
	if post(request):
		nick = 'fld_nick' in request.POST.keys()
		indeks = 'fld_index' in request.POST.keys()
		haslo = 'fld_passF' in request.POST.keys()
		haslo2 = 'fld_passRepeat' in request.POST.keys()
		imie = 'fld_name' in request.POST.keys()
		nazwisko = 'fld_lastName' in request.POST.keys()
		semestr = 'select_semester' in request.POST.keys()
		kierunek = 'select_specialization' in request.POST.keys()
		stopienStudiow = 'select_type' in request.POST.keys()
		regulamin = 'cbox_rules' in request.POST.keys()
		zgoda = 'cbox_permission' in request.POST.keys()
		postPelny = nick & indeks & haslo & haslo2 & imie & nazwisko & semestr & kierunek & stopienStudiow & regulamin & zgoda
		if postPelny:
			nick = request.POST['fld_nick']
			indeks = request.POST['fld_index']
			haslo = request.POST['fld_passF']
			haslo2 = request.POST['fld_passRepeat']
			imie = request.POST['fld_name']
			nazwisko = request.POST['fld_lastName']
			semestr = request.POST['select_semester']
			kierunek = request.POST['select_specialization']
			stopienStudiow = request.POST['select_type']
			poprawnosc = sprawdzDane(nick, imie, nazwisko, indeks, haslo, haslo2, semestr, kierunek, stopienStudiow)
			if(poprawnosc):
				kierunek = models.Kierunek.objects.get(id = request.POST['select_specialization'])
				haslo = sha256_crypt.encrypt(haslo)
				uzytkownik = models.Uzytkownik(nick = nick, imie = imie, nazwisko = nazwisko, haslo = haslo, mail = indeks + "@student.pwr.wroc.pl", aktywator = wygenerujAktywator())
				uzytkownik.save()
				uzytkownik.ktoWprowadzil = models.Uzytkownik.objects.get(id = uzytkownik.id)
				uzytkownik.ktoZmienilDane = models.Uzytkownik.objects.get(id = uzytkownik.id)
				uzytkownik.dataOstLogowania = datetime.date.today()
				uzytkownik.dataOstZmianyHasla = datetime.date.today()
				uzytkownik.dataOstZmianyDanych = datetime.date.today()

				student = models.Student(uzytkownik = models.Uzytkownik.objects.get(id = uzytkownik.id), indeks = indeks, kierunek = kierunek, rodzajStudiow = stopienStudiow, semestr = semestr)
				student.save()
				uzytkownik.domyslny = student.id
				uzytkownik.save()
				wyslijPotwierdzenie(uzytkownik)
				request.session['komRej'] = '1' # Pomyslny przebieg rejestracji
				return HttpResponseRedirect('/')
			else:
				request.session['komRej'] = '2' # Dane nie spelniaja ograniczen
				return HttpResponseRedirect('/')
		else:
			request.session['komRej'] = '3' # Nie podano wszystkich danych
			return HttpResponseRedirect('/')
	else:
		request.session['komRej'] = '4' # Blad wysylania
		return HttpResponseRedirect('/')


# Sprawdzanie poprawności danych przy rejestracji
def sprawdzDane(nick, imie, nazwisko, indeks, haslo, haslo2, semestr, kierunek, stopien):
	nickOk = (nickWolny(nick) & nickPoprawny(nick))
	if nickOk == False:
		return False
		
	if not sprImie(imie):
		return False
		
	if not sprNazwisko(nazwisko):
		return False

	indeksOk = (indeksWolny(indeks) & indeksPoprawny(indeks))
	if indeksOk == False:
		return False
		
	hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', haslo)
	hasloOk = hasloOk & (haslo == haslo2)
	if hasloOk == False:
		return False


	if not sprSemestr(kierunek, stopien, semestr):
		return False
	
	return True


# Sprawdzanie nicku - dozwolne znaki oraz unikatowość w bazie danych
def sprawdzNick(request, nick):
	if (nickPoprawny(nick) & nickWolny(nick)):
		return HttpResponse('okay')
	else:
		return HttpResponse('denied')

	
# Czy nick nie jest zajęty
def nickWolny(nick):
	uzytkownicy = models.Uzytkownik.objects.all()
	for uz in uzytkownicy:
		if nick == uz.nick:
			return False
	return True


# Czy nick jest poprawny - dozwolone znaki
def nickPoprawny(nick):
	ok = len(nick)>=2 & len(nick) <=20
	pattern = '^[A-Za-z0-9_-]*$'
	return pasuje(pattern, nick) & ok

	
# Sprawdzanie indeksu - dozwolne znaki oraz unikatowość w bazie danych
def sprawdzIndeks(request, indeks):
	if (indeksPoprawny(indeks) & indeksWolny(indeks)):
		return HttpResponse('okay')
	else:
		return HttpResponse('denied')


# Czy indeks nie jest zajęty
def indeksWolny(indeks):
	studenci = models.Student.objects.all()
	for st in studenci:
		if indeks == st.indeks:
			return False
	return True


# Czy indeks jest poprawny - dozwolone znaki
def indeksPoprawny(indeks):
	pattern = '\d{6}'
	return pasuje(pattern, indeks)


# Potwierdzenie rejestracji po kliknieciu w link aktywacyjny
def potwierdzRejestracje(request, aktywator, nick):
	try:
		uzytkownik = uz(nick)
		if uzytkownik.aktywator == aktywator:
			uzytkownik.czyAktywowano = True
			uzytkownik.save()
			request.session['content'] = 'portal'
			request.session['komRej'] = '5'
			return HttpResponseRedirect("/")
		else:
			HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")	 #<------------------------- oprogramować wyświetlanie tego!!!!
	except:
		return HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")  #<------------------------- oprogramować wyświetlanie tego!!!!


############### LOGOWANIE ################################################################

# Logowanie	
def logowanie(request):
	if post(request):
		nickPost = request.POST['fld_login']
		hasloPost = request.POST['fld_pass']
		try:
			uzytkownik = models.Uzytkownik.objects.get(nick = nickPost)
			haslo = uzytkownik.haslo
			zgodnosc = sha256_crypt.verify(hasloPost, haslo)
			if(zgodnosc):
				if jestStudentem(uzytkownik):
					domyslny = uzytkownik.domyslny
					student = models.Student.objects.get(id = domyslny)
					if uzytkownik.czyAktywowano:
						if czyZmienicHaslo(uzytkownik):
							request.session['nick'] = nickPost  #Uzyteczne zeby wiedziec dla kogo zmieniamy haslo
							request.session['komunikat'] = '4' # zmiana hasla
						else:
							request.session['studentId'] = student.id
							request.session['content'] = 'news'
							uzytkownik.dataOstLogowania = datetime.datetime.now()
							uzytkownik.save()
							if 'cbox_remember' in request.POST.keys():
								request.session['login'] = nickPost
							else:
								request.session['login'] = ""
					else:
						request.session['komunikat'] = '3' # konto nieaktywne
				else:
					if czyZmienicHaslo(uzytkownik):
						request.session['nick'] = nickPost  #Uzyteczne zeby wiedziec dla kogo zmieniamy haslo
						request.session['komunikat'] = '4' # zmiana hasla
					else:
						request.session['admin'] = nickPost
						request.session['content'] = 'news'
						uzytkownik.dataOstLogowania = datetime.datetime.now()
						uzytkownik.save()
						if 'cbox_remember' in request.POST.keys():
							print('zapamietaj mnie!')
							request.session['login'] = nickPost
						else:
							print('nie pamietaj')
							request.session['login'] = ""
			else:
					request.session['komunikat'] = '2' # bledny login lub haslo
		except:
				request.session['komunikat'] = '2' # bledny login lub haslo
				pass
	else:
			request.session['komunikat'] = '1' # blad wyslania
	return HttpResponseRedirect("/")


# Przypomnienie hasla
def przypomnijHaslo(request):
	if post(request) & ('fld_login' in request.POST.keys()):
		nick = request.POST['fld_login']
		try:
			uzytkownik = uz(nick)
			uzytkownik.aktywator = wygenerujAktywator()
			uzytkownik.save()
			wyslijPrzypHaslo(uzytkownik)
			return HttpResponse("ok")
		except:
			return HttpResponse("Nie ma takiego uzytkownika")
	else:
		return HttpResponse("Dane nie zostały wysłane.")


# Wyslanie maila z przypomnieniem hasła
def wyslijPrzypHaslo(uzytkownik):
    tytul = "PwrTracker - przypomnienie hasła"
    tresc = "Witaj użytkowniku PwrTracker!\n\nAby ustawić nowe hasło w serwisie kliknij w poniższy link.\n"
    tresc = tresc + "http://" + adresSerwera +"/newPassword/" + uzytkownik.aktywator + "/" + uzytkownik.nick.encode('utf-8')
    send_mail(tytul, tresc, 'pwrtracker@gmail.com', [uzytkownik.mail], fail_silently=False)


# Wyswietlenie formularza do ustawiania nowego hasla
def ustawNoweHaslo(request, aktywator, nick):
    try:
        uzytkownik = uz(nick)
        if uzytkownik.aktywator == aktywator:
            request.session['komunikat'] = '4'
            request.session['nick'] = nick
            return HttpResponseRedirect("/")
        else:
            return HttpResponse("Wyświetlenie formularza by ustawić nowe hasło zakoćzyło się niepowodzeniem. Spróbuj jeszcze raz")	#<----- wtf??
    except:
        return HttpResponse("Wyświetlenie formularza by ustawić nowe hasło zakoćzyło się niepowodzeniem. Spróbuj jeszcze raz") #<----- wtf??
    
# Zmiana hasla
def zapiszNoweHaslo(request):
    if post(request) & ('fld_passNew' in request.POST.keys()) & ('fld_passNewRepeat' in request.POST.keys()):
        password = request.POST['fld_passNew']
        password2 = request.POST['fld_passNewRepeat']
        nick = request.session['nick']
        hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', password)
        hasloOk = hasloOk & (password == password2)
        if hasloOk == False:
            return HttpResponseRedirect('Haslo nieprawidlowe') #<----- wtf?????????
        else:
            try:
                uzytkownik = uz(nick)
                if (sha256_crypt.verify(password, uzytkownik.haslo)):
                    return HttpResponse("Haslo nie może być takie same jak poprzednie")
                else:
                    haslo = sha256_crypt.encrypt(password)
                    uzytkownik.haslo = haslo
                    uzytkownik.dataOstZmianyHasla = datetime.date.today();
                    uzytkownik.save()
                #del request.session['komunikat']
            except:
                return HttpResponse("Nie ma takiego uzytkownika")
    return HttpResponse("ok")


# Przeslanie aktywatora ponownie - wygenerowanie nowego
def przeslijAktywatorPonownie(request):
	if post(request) & ('fld_login_ver' in request.POST.keys()):
		nick = request.POST['fld_login_ver']
		try:
			uzytkownik = uz(nick)
			if (uzytkownik.czyAktywowano == False):
				uzytkownik.aktywator = wygenerujAktywator()
				uzytkownik.save()
				wyslijPotwierdzenie(uzytkownik)
			else:
				return HttpResponse("Juz aktywne")
		except:
			return HttpResponse("Nie ma takiego uzytkownika")
	return HttpResponse("ok")
	

# Wylogowanie z serwisu - usunięcie sesji
def wylogowanie(request):
	usunSesje(request)
	return HttpResponseRedirect('/')

############################################# TESTOWANIE ###################################



# Klasa do testow
def test(request):
	if True:
		student = stud(8)
		uzytkownik = student.uzytkownik
		listaUz = [uzytkownik]
		studenci = models.Student.objects.filter(uzytkownik = uzytkownik)
		kierunki = models.Kierunek.objects.filter(student__in = studenci)
		wydzialy = models.Wydzial.objects.filter(kierunek__in = kierunki)
		lista = listaUz + list(studenci) + list(kierunki) + list(wydzialy)
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(lista, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


def test2(request):
	nick = 'ktosik'
	indeks = '899888'
	wydz = models.Wydzial.objects.all()
	return render_to_response('registration.html', {'nick': nick, 'index': indeks, 'wydzialy': wydz})

