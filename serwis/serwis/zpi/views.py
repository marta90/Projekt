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
############### FUNKCJE POMOCNICZE ########################################################

# Pobranie uzytkownika po nicku
def uz(nick):
	return models.Uzytkownik.objects.get(nick=nick)

# Pobranie studenta po id
def stud(ids):
	return models.Student.objects.get(id = ids)

# Pobranie uzytkownika zapamietanego w sesji
def uzSesja(request):
	return studSesja(request).uzytkownik

# Pobranie uzytkownika z nicku wyslanego postem
def uzPost(request):
	return studPost(request).uzytkownik

# Pobranie studenta zapamietanego w sesji
def studSesja(request):
	return stud(request.session['studentId'])

# Pobranie studenta z nicku wyslanego postem
def studPost(request):
	return stud(request.POST['studentId'])


# Sprawdzenie czy dane wyslano metoda post
def post(request):
	if request.method == 'POST':
		return True
	else:
		return False

	
# Sprawdzenie czy sesja jest otwarta
def jestSesja(request):
	return ('studentId' in request.session or 'admin' in request.session)


# Usuniecie polskich znakow z wybranego tekstu
def usunPolskieZnaki(text):
	pltoang_tab = {u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ż':'z', u'ź':'z'}
	return ''.join( pltoang_tab.get(char, char) for char in text )


def saWPoscie(request, dane):
	for d in dane:
		if d not in request.POST.keys():
			return False
		else:
			return True

############### STRONA GLOWNA #############################################################

# Wyswietlenie strony glownej
def glowna(request):
	# Uzytkownik jest zalogowany
	if jestSesja(request):
		nick = uzSesja(request).nick
		if 'content' not in request.session.keys():
			request.session['content'] = 'news'
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
	else:
		if 'content' not in request.session.keys():
			request.session['content'] = 'portal'
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
		return HttpResponse("Nie sprawdzono poprawności loginu oraz numer indeksu.")

'''
#Pobranie kierunków dla okreslonych wydzialow. Potrzebne przy rejestracji
def pobierzKierunki(request, idWydz):
	kierunki = models.Kierunek.objects.filter(wydzial__id=idWydz)
	odp = ''
	for k in kierunki:
		odp = odp + '<option value=\'' + str(k.id) +'\'>' + k.nazwa + '</option>'
	return HttpResponse(odp)
'''

def pobierzKierunki(request, idWydzialu):
	kierunki = models.Kierunek.objects.filter(wydzial__id = idWydzialu)
	odp = ""
	for k in kierunki:
		odp = odp + 'obj.options[obj.options.length] = new Option(\''+ k.nazwa +'\' , \'' + str(k.id) + '\'); '
	return HttpResponse(odp)

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

'''
#Pobieranie Semestrów dla poszczególnych kierunków i typu studiów. Potrzebne przy rejestracji
def pobierzSemestry(request, idSpec, idTyp):
	kierunek = models.Kierunek.objects.get(id = idSpec)
	odp = ""
	if idTyp == "1":
		for i in range(1, kierunek.liczbaSemestrow1st + 1):
			odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
	if idTyp == "2":
		for i in range(1, kierunek.liczbaSemestrow2stPoInz + 1):
			odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
	return HttpResponse(odp)
'''

# Rejestracja użytkownika
@transaction.commit_on_success
def zarejestruj(request):
	usunSesje(request)
	if post(request):
		nick = 'fld_nick' in request.POST.keys()
		indeks = 'fld_index' in request.POST.keys()
		haslo = 'fld_pass' in request.POST.keys()
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
			haslo = request.POST['fld_pass']
			haslo2 = request.POST['fld_passRepeat']
			imie = request.POST['fld_name']
			nazwisko = request.POST['fld_lastName']
			semestr = request.POST['select_semester']
			kierunek = request.POST['select_specialization']
			stopienStudiow = request.POST['select_type']
			poprawnosc = sprawdzDane(nick, imie, nazwisko, indeks, haslo, haslo2, semestr, kierunek, stopienStudiow)
			if(poprawnosc):
				kierunek = kier(request.POST['select_specialization'])
				haslo = sha256_crypt.encrypt(haslo)
				uzytkownik = models.Uzytkownik(nick = nick, imie = imie, nazwisko = nazwisko, haslo = haslo, mail = indeks + "@student.pwr.wroc.pl")
				uzytkownik.save(commit = False)
				uzytkownik.ktoWprowadzil = models.Uzytkownik.objects.get(id = uzytkownik.id)
				uzytkownik.ktoZmienilDane = models.Uzytkownik.objects.get(id = uzytkownik.id)
				uzytkownik.dataOstLogowania = datetime.date.today()
				uzytkownik.dataOstZmianyHasla = datetime.date.today()
				uzytkownik.dataOstZmianyDanych = datetime.date.today()
				uzytkownik.aktywator = wygenerujAktywator()
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
		
	imieOk = pasuje("^([a-zA-Z '-]+)$", imie)
	if imieOk == False | len(imie)<2:
		return False
		
	nazwiskoOk = pasuje("^([a-zA-Z '-]+)$", nazwisko)
	if nazwiskoOk == False | len(nazwisko)<2:
		return False
		
	indeksOk = (indeksWolny(indeks) & indeksPoprawny(indeks))
	if indeksOk == False:
		return False
		
	hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', haslo)
	hasloOk = hasloOk & (haslo == haslo2)
	if hasloOk == False:
		return False
	
	try:
		kierunekOk = kier(kierunek)
	except:
		return False
	
	stopienInt = pasuje('\d+', stopien)
	semestrInt = pasuje('\d+', semestr)
	if ((stopienInt == False) | (semestrInt == False)):
		return False	
	if (int(stopien) == 1):
		max = kierunekOk.liczbaSemestrow1st
		if(int(semestr) > max | int(semestr) < 1 ):
			return False
	elif (int(stopien) == 2):
		max = kierunekOk.liczbaSemestrow2stPoInz
		if(int(semestr) > max | int(semestr) < 1 ):
			return False
	else:
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


# Funkcja sprawdzajace dopasowanie tekstu do wzorca
def pasuje(wzorzec, tekst):
	if (re.match(wzorzec, tekst)):
		return True
	else:
		return False


# Generacja kodu do aktywacji konta
def wygenerujAktywator():
	allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
	import random
	random = random.SystemRandom()
	return ''.join([random.choice(allowed_chars) for i in range(33)])


# Wyslanie maila z kodem potwierdzajacym rejestracje
def wyslijPotwierdzenie(uzytkownik):
	tytul = "PwrTracker - potwierdzenie rejestracji"
	tresc = "Witaj na PwrTracker!\n\nAby potwierdzić rejestrację w serwisie kliknij na poniższy link.\n"
	tresc = tresc + "http://87.99.21.160:7272/confirm/" + uzytkownik.aktywator + "/" + uzytkownik.nick.encode('utf-8')
	#send_mail(tytul, tresc, 'pwrtracker@gmail.com', [uzytkownik.mail], fail_silently=False)

	
# Potwierdzenie rejestracji po kliknieciu w link aktywacyjny
def potwierdzRejestracje(request, aktywator, nick):
	try:
		uzytkownik = uz(nick)
		if uzytkownik.aktywator == aktywator:
			uzytkownik.czyAktywowano = True
			uzytkownik.save()
			return HttpResponse("Udało się aktywować")
		else:
			HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")	
	except:
		return HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")		


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
			print('Haslo w poscie ' + hasloPost)
			print('Haslo w bazie ' + haslo)
			if(zgodnosc):
				print('zgodnosc przy logowaniu')
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
					else:
						request.session['komunikat'] = '3' # konto nieaktywne
				else:
					if czyZmienicHaslo(uzytkownik):
						request.session['nick'] = nickPost  #Uzyteczne zeby wiedziec dla kogo zmieniamy haslo
						request.session['komunikat'] = '4' # zmiana hasla
					else:
						request.session['admin'] = nickPost
						request.session['content'] = 'news'
			else:
					request.session['komunikat'] = '2' # bledny login lub haslo
		except:
				request.session['komunikat'] = '2' # bledny login lub haslo
				pass
	else:
			request.session['komunikat'] = '1' # blad wyslania
	return HttpResponseRedirect("/")


# Sprawdzenie czy dany uzytkownik jest studentem	
def jestStudentem(uzytkownik):
	student = models.Student.objects.filter(uzytkownik=uzytkownik)
	if student.exists():
		return True
	else:
		return False


# Sprawdzenie czy dany uzytkownik musi zmienić hasło (mineło 30 dni)
def czyZmienicHaslo(uzytkownik):
	dzisiaj = datetime.date.today()
	dataZmianyHasla = uzytkownik.dataOstZmianyHasla.date()
	dni = (dzisiaj - dataZmianyHasla)
	if(dni.days) > 29:
		return True
	else:
		return False
	

# Funkcja do oprogramowania
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
    tresc = tresc + "http://127.0.0.1:8000/newPassword/" + uzytkownik.aktywator + "/" + uzytkownik.nick.encode('utf-8')
    indeks = models.Student.objects.filter(uzytkownik = uzytkownik.id)[0].indeks
    send_mail(tytul, tresc, 'pwrtracker@gmail.com', [indeks + "@student.pwr.wroc.pl"], fail_silently=False)

# wyswietlenie formularza by ustawic nowe haslo
def ustawNoweHaslo(request, aktywator, nick):
    try:
        uzytkownik = uz(nick)
        if uzytkownik.aktywator == aktywator:
            request.session['komunikat'] = '4'
            request.session['nick'] = nick
            return HttpResponseRedirect("/")
        else:
            return HttpResponse("Wyświetlenie formularza by ustawić nowe hasło zakoćzyło się niepowodzeniem. Spróbuj jeszcze raz")	
    except:
        return HttpResponse("Wyświetlenie formularza by ustawić nowe hasło zakoćzyło się niepowodzeniem. Spróbuj jeszcze raz")
    
def zapiszNoweHaslo(request):
    if post(request) & ('fld_passNew' in request.POST.keys()) & ('fld_passNewRepeat' in request.POST.keys()):
        password = request.POST['fld_passNew']
        password2 = request.POST['fld_passNewRepeat']
        nick = request.session['nick']
        hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', password)
        hasloOk = hasloOk & (password == password2)
        if hasloOk == False:
            return HttpResponseRedirect('Haslo nieprawidlowe')
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


def usunSesje(request):
	try:
		for elemSesji in request.session.keys():
			del request.session[elemSesji]
	except KeyError:
		pass

############### PORTAL ####################################################################

# Zaladowanie strony portal.html do diva na stronie glownej
def zaladujPortal(request):
	if jestSesja(request):
		return zaladujNewsy(request)
	elif 'komRej' in request.session:
		kom = request.session['komRej']
		# Poprawny przebieg rejestracji
		if kom == '1':
			tekst = "Na Twojego maila studenckiego został wysłany link z aktywacją konta. <br> Kliknij go, aby potwierdzić rejestrację w serwisie."

		# Dane nie spelniaja ograniczen
		elif kom == '2':
			tekst = "Dane nie spełniają wymaganych ograniczeń. Spróbuj ponownie."
		
		# Nie przesłano wszystkich danych
		elif kom == '3':
			tekst = "Nie wysłano wszystkich danych. Spróbuj ponownie."
		
		# Blad wysylania	
		elif kom == '4':
			tekst = "Wystąpił błąd podczas rejestracji. Spróbuj ponownie."
		
		usunSesje(request)
		return render_to_response('portal.html', {'alert':tekst})	
	else:
		return render_to_response('portal.html')


# Zaladowanie strony z aktualnosciami (shoutbox, moje wydarzenia, ostatnio dodane wydarzenia) na stronie glownej
def zaladujNewsy(request):
	student = studSesja(request)
	kierunek = student.kierunek
	semestr = student.semestr
	stopien = student.rodzajStudiow
	shoutbox = models.Shoutbox.objects.filter(student__kierunek = kierunek,
											  student__semestr = semestr,
											  student__rodzajStudiow = stopien).order_by('data')[:10]
	shoutbox = shoutbox.reverse()
	uzytkownik = student.uzytkownik
	wczoraj = datetime.date.today() - datetime.timedelta(days=1)
	ileWydarzen = uzytkownik.ileMoichWydarzen
	mojeWydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gt = wczoraj).order_by('dataWydarzenia')[:ileWydarzen]
	wydarzenia = filtrujNoweWydarzenia(request)
	wydarzeniaUz = uzytkownik.wydarzenie_set.all()
	wydarzenia = wydarzenia.exclude(id__in=wydarzeniaUz) 
	wydarzenia = wydarzenia.order_by('-dataDodaniaWyd')[:10]
	dzisiaj = datetime.datetime.now()
	wczoraj = dzisiaj - datetime.timedelta(days = 1)
	return render_to_response('news.html', {'rozmowy':shoutbox, 'mojeWydarzenia':mojeWydarzenia, 'wydarzenia':wydarzenia, 'dzisiaj':dzisiaj, 'wczoraj':wczoraj})


# Pobranie aktualnego shoutboxa - potrzebne przy odświeżaniu go
def zaladujShoutbox(request):
	student = studSesja(request)
	kierunek = student.kierunek
	semestr = student.semestr
	stopien = student.rodzajStudiow
	shoutbox = models.Shoutbox.objects.filter(student__kierunek = kierunek,
											  student__semestr = semestr,
											  student__rodzajStudiow = stopien).order_by('data')[:10]
	shoutbox = shoutbox.reverse()
	dzisiaj = datetime.datetime.now()
	wczoraj = dzisiaj - datetime.timedelta(days=1)
	return render_to_response('shoutbox.html', {'rozmowy':shoutbox, 'dzisiaj':dzisiaj, 'wczoraj':wczoraj})


# Dodanie wiadomosci do shoutboxa
def dodajShout(request, wiadomosc):
	student = studSesja(request)
	if wiadomosc != "":
		shout = models.Shoutbox(student = student,
								tresc = wiadomosc,
								data = datetime.datetime.now(),
								czyWazne = False)
		shout.save()
	return HttpResponseRedirect("/media/html/shoutbox.html")


def dodajWydDoKalendarza(request, idWyd):
	try:
		uzytkownik = uzSesja(request)
		wydarzenie = models.Wydarzenie.objects.get(id = idWyd)
		if (wydarzenie not in uzytkownik.wydarzenie_set.all()):
			kalendarz = models.Kalendarz(uzytkownik = uzytkownik, wydarzenie = wydarzenie, opis = wydarzenie.opis)
			kalendarz.save()
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')
		

def filtrujNoweWydarzenia(request):
    student = studSesja(request)
    uzytkownik = uzSesja(request)
    kierStudenta = student.kierunek
    wydzStudenta = student.kierunek.wydzial
    semStudenta = student.semestr
    rodzStudenta = student.rodzajStudiow
    wydarzenia = models.Wydarzenie.objects.filter((Q(dodal__kierunek = kierStudenta) & Q(rodzajWydarzenia = 3)) | (Q(dodal__kierunek__wydzial = wydzStudenta) & Q(rodzajWydarzenia = 2)) |
                                                  (Q(rodzajWydarzenia = 1)) | (Q(grupa__uzytkownik = uzytkownik) & Q(rodzajWydarzenia = 4)) |
                                                  (Q(dodal__semestr = semStudenta) & Q(dodal__rodzajStudiow = rodzStudenta) & Q(dodal__kierunek = kierStudenta)& Q(rodzajWydarzenia = 5)) )
    return wydarzenia


############### PLAN ZAJEC ################################################################


# Zaladowanie strony timetable.html do diva na stronie glownej
def zaladujPlan(request):
	if jestSesja(request):
		st = studSesja(request)
		uz = st.uzytkownik
		planPn = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'pn').order_by('grupa__godzinaOd')
		planWt = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'wt').order_by('grupa__godzinaOd')
		planSr = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'śr').order_by('grupa__godzinaOd')
		planCzw = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'cz').order_by('grupa__godzinaOd')
		planPi = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'pt').order_by('grupa__godzinaOd')
		czy = False
		if(len(planPn) != 0 or len(planWt) != 0 or len(planSr) != 0 or len(planCzw) != 0 or len(planPi) != 0):
			czy = True
		#return HttpResponse()
		 #and planWt.count==0 and planSr.count==0 and planCzw.count==0 and planPi.count==0
		return render_to_response('timetable2.html', {'czyJestPlan':czy, 'pPn':planPn, 'pWt':planWt, 'pSr':planSr, 'pCz':planCzw, 'pPi':planPi})
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")

def pobierzZajecia(request, start, end):
    if jestSesja(request):
        st = studSesja(request)
        uz = st.uzytkownik
        wynik = ""          #Zmienna tymczasowa
        output = {          # Wynik jaki zostanie wyslany jsonem
            "events": []
        }
        start = start.split("-")        # rozdzielam przeslana mi date startu
        end = end.split("-")            # rozdzielam przeslana mi date konca
        startDate = datetime.date(int(start[0]),int(start[1])+1,int(start[2]))  # tworze date jako obiekt datetime.date
        endDate = datetime.date(int(end[0]),int(end[1])+1,int(end[2]))
        czyParzysty = czyParzystyTydzien(startDate)                             # sprawdzam czy tydzien jest tygodniem parzystym
        planPn = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'pn').order_by('grupa__godzinaOd')   # pobieram z bazy zajecia
        planWt = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'wt').order_by('grupa__godzinaOd')
        planSr = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'śr').order_by('grupa__godzinaOd')
        planCzw = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'cz').order_by('grupa__godzinaOd')
        planPi = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'pt').order_by('grupa__godzinaOd')
        for i in range(0, 5):       # petla od 0 do 4 
            nowaData = startDate + datetime.timedelta(days=i)   # dodaje do daty poczatkowej okreslona ilosc dni, aby odnalezc wszystkie dni tygodnia
            if nowaData.strftime("%w") == '1':        #poniedzialek
                utworzZajecia(planPn, output, nowaData, czyParzysty, wynik)     # utworzenie zajec z poniedzialku
            if nowaData.strftime("%w") == '2':        #wtorek
                utworzZajecia(planWt, output, nowaData, czyParzysty, wynik)
            if nowaData.strftime("%w") == '3':        #sroda
                utworzZajecia(planSr, output, nowaData, czyParzysty, wynik)
            if nowaData.strftime("%w") == '4':        #czwartek
                utworzZajecia(planCzw, output, nowaData, czyParzysty, wynik)
            if nowaData.strftime("%w") == '5':        #piatek
                utworzZajecia(planPi, output, nowaData, czyParzysty, wynik)
        
        #return HttpResponse(wynik)
        return HttpResponse(simplejson.dumps(output), mimetype="application/json")
        
def utworzZajecia(plan, output, nowaData, czyParzysty, wynik):
    for i in range(0, len(plan)):       # przechodze po liscie zajec
        if (plan[i].grupa.godzinaOd != None):         # sprawdzam czy maja godzine i 
            if (plan[i].grupa.parzystosc == ''):      # czy nie maja okreslonej parzystosci
                tworzenieZajec(i, nowaData, plan, output)                                   # tworze dla znalezionych zajec json
            else:
                if((plan[i].grupa.parzystosc == 'TN') & (czyParzysty == False)):            # sprawdzam czy tydzien jest nie parzysty i dodaje te zajecia
                    tworzenieZajec(i, nowaData, plan, output)
                if((plan[i].grupa.parzystosc == 'TP') & (czyParzysty == True)):             # sprawdzam czy tydzien jest parzysty i dodaje te zajecia
                    tworzenieZajec(i, nowaData, plan, output)

def tworzenieZajec(i, nowaData, plan, output):      # tworze json i dodaje go do listy events
    event = {"id": str(i),
                    "start": "" + str(nowaData.year) + ":" + str(nowaData.month -1) + ":" + str(nowaData.day) + ":" + str(plan[i].grupa.godzinaOd.hour) + ":" + str(plan[i].grupa.godzinaOd.minute),
                    "end": "" + str(nowaData.year) + ":" + str(nowaData.month -1) + ":" + str(nowaData.day) + ":" + str(plan[i].grupa.godzinaDo.hour) + ":" + str(plan[i].grupa.godzinaDo.minute),
                    "title": "(" + plan[i].grupa.kurs.rodzaj + ") " +  plan[i].grupa.kurs.nazwa + "<br>" + plan[i].grupa.prowadzacy.tytul + " " +
                                plan[i].grupa.prowadzacy.imie + " " + plan[i].grupa.prowadzacy.nazwisko + "<br>" + plan[i].grupa.miejsce  + ", " + plan[i].grupa.godzinaOd.strftime('%H:%M') + "-" + plan[i].grupa.godzinaDo.strftime('%H:%M')
                                            }
    output.get("events").append(event)
    

def czyParzystyTydzien(data):           # sprawdzam czy tydzien jest parzysty
    if (int(data.strftime("%W")) % 2 == 0):
        return True
    else:
        return False


############### WYKLADOWCY #################################################################

# Zaladowanie strony teachers.html do diva na stronie glownej - wyswietlenie wykladowcow na litere A
def zaladujWykladowcow(request):
	literaDuza = "A"
	literaMala = literaDuza.lower()
	wykladowcy = models.Prowadzacy.objects.extra(select={'nazwiskoD': 'upper(nazwisko)', 'imieD': 'upper(imie)'}).filter( Q(nazwisko__startswith=literaDuza) | Q(nazwisko__startswith=literaMala)).order_by('nazwiskoD', 'imieD')
	return render_to_response('teachers.html', {'prowadzacy':wykladowcy})


# Pobranie wykladowcy, ktorego nazwisko rozpoczyna sie na wybrana litere
def wykladowcaNaLitere(request, litera):
	literaDuza = litera
	literaMala = litera.lower()
	wykladowcy = models.Prowadzacy.objects.extra(select={'nazwiskoD': 'upper(nazwisko)', 'imieD': 'upper(imie)'}).filter( Q(nazwisko__startswith=literaDuza) | Q(nazwisko__startswith=literaMala)).order_by('nazwiskoD', 'imieD')
	return render_to_response('teachersList.html', {'prowadzacy':wykladowcy})


# Wyszukanie wykladowcy po wybranej frazie
def znajdzWykladowce(request, nazwa):
	wykladowcy = models.Prowadzacy.objects.extra(select={'nazwiskoD': 'upper(nazwisko)', 'imieD': 'upper(imie)'}).order_by('nazwiskoD', 'imieD')
	wyrazy = nazwa.split()

	calosc = ""
	for i in range(len(wyrazy)):
		wyrazy[i] = usunPolskieZnaki(wyrazy[i]).upper()
		calosc = calosc + wyrazy[i] + " "
	calosc = calosc[:-1]
	ilosc = len(wyrazy)
	wynik = []
	propozycje = []
	for w in wykladowcy:
		imie = usunPolskieZnaki(w.imie).upper()
		nazwisko = usunPolskieZnaki(w.nazwisko).upper()
		imieNazwisko = imie + " " + nazwisko
		nazwiskoImie = nazwisko + " " + imie
		# Pełne imię i nazwisko
		if(imieNazwisko == calosc or nazwiskoImie == calosc or nazwisko == calosc or imie == calosc):
			wynik.append(w)
		else:
			for wyr in wyrazy:
				if(wyr in imieNazwisko):
					propozycje.append(w)
	
	if(len(wynik)>0):	
		return render_to_response('teachersList.html', {'prowadzacy':wynik})
	elif(len(propozycje)>0):
		return render_to_response('teachersList.html', {'prowadzacy':propozycje, 'tekst':"Czy chodziło Ci o..."})
	else:
		return render_to_response('teachersList.html', {'tekst':"Nie znaleziono wyników spełniających podane kryteria. Spróbuj ponownie."})


# Wczytanie konsultacji podanego wykladowcy
def konsultacjeWykladowcy(request, idw):
	prowadzacy = models.Prowadzacy.objects.get(id = idw)
	konsultacje = models.Konsultacje.objects.filter(prowadzacy = prowadzacy)
	response = HttpResponse()
	response.write("<i>")
	br = False
	if konsultacje.exists():
		for k in konsultacje:
			if br:
				response.write('<br>')
			br = True
			response.write(k.dzienTygodnia)
			if (k.parzystosc == 'TP') or (k.parzystosc == 'TN'):
				response.write(" " + k.parzystosc)
			response.write(" " + k.godzinaOd.strftime("%H:%M") + " - " + k.godzinaDo.strftime("%H:%M") + ", bud. ")
			response.write(k.budynek.nazwa + ", s. " + k.sala)
		
	else:
		response.write('Brak informacji o konsultacjach')
	#response.write('</i> &nbsp &nbsp   <img id = "a' +idw +'" src="media/html/img/edit.png" height=20px width=20px onclick="editIt(this);">')
	response.write('</i><br>')
	response.write(' <a href=# id= "' + idw + '" onclick="showPlan(this)">----> Zobacz plan </a>')
	return response


def pobierzZajeciaWykladowcy(request, idw, start, end):
    prowadzacy = models.Prowadzacy.objects.get(id = idw)
    wynik = ""          #Zmienna tymczasowa
    output = {          # Wynik jaki zostanie wyslany jsonem
        "events": []
    }
    start = start.split("-")        # rozdzielam przeslana mi date startu
    end = end.split("-")            # rozdzielam przeslana mi date konca
    startDate = datetime.date(int(start[0]),int(start[1])+1,int(start[2]))  # tworze date jako obiekt datetime.date
    endDate = datetime.date(int(end[0]),int(end[1])+1,int(end[2]))
    czyParzysty = czyParzystyTydzien(startDate)                             # sprawdzam czy tydzien jest tygodniem parzystym
    grupyPn = models.Grupa.objects.filter(prowadzacy = prowadzacy, dzienTygodnia = 'pn')
    grupyWt = models.Grupa.objects.filter(prowadzacy = prowadzacy, dzienTygodnia = 'wt')
    grupySr = models.Grupa.objects.filter(prowadzacy = prowadzacy, dzienTygodnia = 'śr')
    grupyCzw = models.Grupa.objects.filter(prowadzacy = prowadzacy, dzienTygodnia = 'cz')
    grupyPi = models.Grupa.objects.filter(prowadzacy = prowadzacy, dzienTygodnia = 'pt')
    for i in range(0, 5):       # petla od 0 do 4 
        nowaData = startDate + datetime.timedelta(days=i)   # dodaje do daty poczatkowej okreslona ilosc dni, aby odnalezc wszystkie dni tygodnia
        if nowaData.strftime("%w") == '1':        #poniedzialek
            utworzZajeciaProw(grupyPn, output, nowaData, czyParzysty, wynik)     # utworzenie zajec z poniedzialku
        if nowaData.strftime("%w") == '2':        #wtorek
            utworzZajeciaProw(grupyWt, output, nowaData, czyParzysty, wynik)
        if nowaData.strftime("%w") == '3':        #sroda
            utworzZajeciaProw(grupySr, output, nowaData, czyParzysty, wynik)
        if nowaData.strftime("%w") == '4':        #czwartek
            utworzZajeciaProw(grupyCzw, output, nowaData, czyParzysty, wynik)
        if nowaData.strftime("%w") == '5':        #piatek
            utworzZajeciaProw(grupyPi, output, nowaData, czyParzysty, wynik)
    
    #return HttpResponse(wynik)
    return HttpResponse(simplejson.dumps(output), mimetype="application/json")

def utworzZajeciaProw(grupy, output, nowaData, czyParzysty, wynik):
    for i in range(0, len(grupy)):       # przechodze po liscie zajec
        if (grupy[i].godzinaOd != None):         # sprawdzam czy maja godzine i 
            if (grupy[i].parzystosc == ''):      # czy nie maja okreslonej parzystosci
                tworzenieZajecProw(i, nowaData, grupy, output)                                   # tworze dla znalezionych zajec json
            else:
                if((grupy[i].parzystosc == 'TN') & (czyParzysty == False)):            # sprawdzam czy tydzien jest nie parzysty i dodaje te zajecia
                    tworzenieZajecProw(i, nowaData, grupy, output)
                if((grupy[i].parzystosc == 'TP') & (czyParzysty == True)):             # sprawdzam czy tydzien jest parzysty i dodaje te zajecia
                    tworzenieZajecProw(i, nowaData, grupy, output)

def tworzenieZajecProw(i, nowaData, grupy, output):      # tworze json i dodaje go do listy events
    event = {"id": str(i),
                    "start": "" + str(nowaData.year) + ":" + str(nowaData.month -1) + ":" + str(nowaData.day) + ":" + str(grupy[i].godzinaOd.hour) + ":" + str(grupy[i].godzinaOd.minute),
                    "end": "" + str(nowaData.year) + ":" + str(nowaData.month -1) + ":" + str(nowaData.day) + ":" + str(grupy[i].godzinaDo.hour) + ":" + str(grupy[i].godzinaDo.minute),
                    "title": "(" + grupy[i].kurs.rodzaj + ") " +  grupy[i].kurs.nazwa + "<br>" + grupy[i].miejsce + "<br>" + grupy[i].godzinaOd.strftime('%H:%M') + "-" + grupy[i].godzinaDo.strftime('%H:%M')
                    }
    output.get("events").append(event)

############### KALENDARZ #################################################################

# Zaladowanie strony calendar.html do diva na stronie glownej
def zaladujKalendarz(request):
	if jestSesja(request):
		return render_to_response('calendar.html')
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")



############### MAPA ######################################################################

# Zaladowanie strony map.html do diva na stronie glownej
def zaladujMape(request):
	return render_to_response('map.html')



############### EDYCJA KONTA ##############################################################

def zaladujZmianaHasla(request):
	return render_to_response('changePassword.html')

def testphp(request):
	for x in request.POST:
		print(request.POST[x])
	return HttpResponse('ok')

# Zaladowanie strony account.html do diva na stronie glownej
def zaladujKonto(request):
	student = studSesja(request)
	uzytkownik = student.uzytkownik
	studenci = models.Student.objects.filter(uzytkownik = uzytkownik)
	wydzialy = models.Wydzial.objects.all()
	return render_to_response('account.html', {'studenci':studenci, 'uzytkownik':uzytkownik, 'wydzialy':wydzialy})


def edytujDane(request):
	if post(request):
		print("----------------------------------------------")
		print('W poscie otrzymano nastepujace klucze:')
		student = studSesja(request)
		uzytkownik = student.uzytkownik
		bledy = []
	
		dane = request.POST.copy()
		for d in dane:
			print d
			
		print(" ")
		
		zmianaHasla = False
		if 'imie' in dane:
			print('Sprawdzam imie...')
			if sprImie(dane['imie']):
				uzytkownik.imie = dane['imie']
				print('Imie ok')
			else:
				print('blad w imieniu')
				bledy.append('imie ')
		
		if 'nazwisko' in dane:
			print('Sprawdzam nazwisko...')
			if sprNazwisko(dane['nazwisko']):
				uzytkownik.nazwisko = dane['nazwisko']
				print('Nazwisko ok')
			else:
				print('blad w nazwisku')
				bledy.append('nazwisko ')
		
				
		if 'haslo' in dane and 'haslo2' in dane and 'stareHaslo' in dane:
			print('Sprawdzam hasla...')
			if sprHasloZeStarym(dane['haslo'], dane['haslo2'], dane['stareHaslo'], uzytkownik.haslo):
				if not sha256_crypt.verify(dane['haslo'], uzytkownik.haslo):
					uzytkownik.haslo = sha256_crypt.encrypt(dane['haslo'])
					zmianaHasla = True
					print('Haslo ok')
			else:
				print('blad w hasle')
				bledy.append('haslo ')
		
		
				
		if 'semestr' in dane and 'kierunek' in dane and 'stopien' in dane:
			print('Sprawdzam semestr itp...')
			if sprSemestr(dane['kierunek'], dane['stopien'], dane['semestr']):
				student.semestr = int(dane['semestr'])
				print('kierunek przed ' + str(student.kierunek_id))
				print('kierunek w poscie ' + dane['kierunek'])
				student.kierunek_id = int(dane['kierunek'])
				print('kierunek po ' + str(student.kierunek_id))
				student.rodzajStudiow = int(dane['stopien'])
				print('Semestr ok')
			else:
				print('blad w semestrze lub podobnych')
				bledy.append('semestr ')
				
				
		if 'ileWydarzen' in dane:
			print('Sprawdzam wydarzenia...')
			if sprWydarzenia(dane['ileWydarzen']):
				uzytkownik.ileMoichWydarzen = int(dane['ileWydarzen'])
				print('Wydarzenia ok')
			else:
				print('blad w ilosci wydarzen')
				bledy.append('ileWydarzen ')
	
		print ('Razem bledow')
		print(len(bledy))
		

		
		if len(bledy) == 0:
			print('nie bylo bledow')
			
			if zmianaHasla:
				uzytkownik.dataOstZmianyHasla = datetime.date.today()	
			uzytkownik.ktoZmienilDane.id = student.uzytkownik.id
			uzytkownik.dataOstZmianyDanych = datetime.date.today()
			print('mhmm')
			student.save()
			uzytkownik.save()
			
			
			
		return HttpResponse(bledy)



def edytujDane2(request):
	if post(request):
		student = studPost(request)
		dane = ['fld_old_pass', 'fld_new_pass', 'fld_new_pass2', 'fld_name', 'fld_lastName', 'select_semester', 'select_specialization', 'select_type', 'sbox_events']
		postPelny = saWPoscie(request, dane)
		if postPelny:
			stareHaslo = request.POST['fld_old_pass']
			haslo = request.POST['fld_new_pass']
			haslo2 = request.POST['fld_new_pass2']
			imie = request.POST['fld_name']
			nazwisko = request.POST['fld_lastName']
			semestr = request.POST['select_semester']
			kierunek = request.POST['select_specialization']
			stopienStudiow = request.POST['select_type']
			ileWydarzen = request.POST['sbox_events']
			poprawnosc = sprawdzDaneDoEdycji(imie, nazwisko, haslo, haslo2, stareHaslo, semestr, kierunek, stopienStudiow, ileWydarzen, hasloUzytkownika)
			if(poprawnosc):
				
				zmianaHasla = False
				
				if student.uzytkownik.imie != imie:
					student.uzytkownik.imie = imie
				
				if student.uzytkownik.nazwisko != nazwisko:
					student.uzytkownik.nazwisko = nazwisko
				
				if not sha256_crypt.verify(haslo, student.uzytkownik.haslo):
					student.uzytkownik.haslo = sha256_crypt.encrypt(haslo)
					zmianaHasla = True
					
				if student.semestr != semestr:
					student.semestr = semestr
					
				if student.kierunek.id != kierunek:
					student.kierunek.id = kierunek
				
				if student.rodzajStudiow != stopienStudiow:
					student.rodzajStudiow = stopienStudiow
					
				if student.uzytkownik.ileMoichWydarzen != ileWydarzen:
					student.uzytkownik.ileMoichWydarzen = ileWydarzen
					
				if zmianaHasla:
					uzytkownik.dataOstZmianyHasla = datetime.date.today()
				
				student.uzytkownik.ktoZmienilDane = student.uzytkownik.id
				student.uzytkownik.dataOstZmianyDanych = datetime.date.today()				
				student.save()
				student.uzytkownik.save()
								
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


def sprImie(imie):
	imieOk = pasuje("^([a-zA-Z '-]+)$", imie)
	return imieOk and len(imie)>=2


def sprNazwisko(nazwisko):
	nazwiskoOk = pasuje("^([a-zA-Z '-]+)$", nazwisko)
	return nazwiskoOk and len(nazwisko)>=2

def sprHasloZeStarym(haslo, haslo2, stareHaslo, hasloUz):
	print('1')
	hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', haslo)
	print('2')
	hasloOk = hasloOk and (haslo == haslo2)
	print('3')
	hasloOk = hasloOk and sha256_crypt.verify(stareHaslo, hasloUz)
	print('4')
	return hasloOk

def sprWydarzenia(ileWydarzen):
	wydarzeniaOk = (ileWydarzen == '0' or ileWydarzen == '1' or ileWydarzen == '3' or ileWydarzen == '7' or ileWydarzen == '14' or ileWydarzen == '28')
	return wydarzeniaOk

def sprSemestr(kierunek, stopien, semestr):
	try:
		kierunekOk = models.Kierunek.objects.get(id = kierunek)
	except:
		return False
	
	stopienInt = pasuje('\d+', stopien)
	semestrInt = pasuje('\d+', semestr)
	if ((stopienInt == False) | (semestrInt == False)):
		return False	
	if (int(stopien) == 1):
		max = kierunekOk.liczbaSemestrow1st
		if(int(semestr) > max | int(semestr) < 1 ):
			return False
	elif (int(stopien) == 2):
		max = kierunekOk.liczbaSemestrow2stPoInz
		if(int(semestr) > max | int(semestr) < 1 ):
			return False
	else:
		return False
	return True

#Wysyłanie maila do admina
def wyslijEmailZProsba(request):
	try:
		do = "pwrtracker@gmail.com"
		od = "pwrtracker@gmail.com"
		mailZwrotny = uzSesja(request).mail.encode('utf-8')
		tresc = request.POST['textarea_request'].encode('utf-8')
		'''
		send_mail('Prośba o edycję konta', tresc+ "\n\nWiadomość wysłana od\n" + mailZwrotny, od, [do], fail_silently=False)
		send_mail("PwrTracker - prośba o edycję danych.",
				  "Wysłałeś wiadomość o następującej treści:\n\n" + tresc,
				  od,
				  [mailZwrotny],
				  fail_silently=False)
		'''
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')
	
	


############### INNE ######################################################################



#Wysyłanie maila do admina
def wyslijEmail(request):
	if post(request):
		do = "pwrtracker@gmail.com"
		od = "pwrtracker@gmail.com"
		mailZwrotny = request.POST['fld_email'].encode('utf-8')
		tytul = request.POST['fld_topic'].encode('utf-8')
		tresc = request.POST['fld_text'].encode('utf-8')
		send_mail(tytul, tresc+ "\n\nWiadomość wysłana od\n" + mailZwrotny, od, [do], fail_silently=False)
		send_mail("PwrTracker - wysłano wiadomość: " + tytul,
				  "Wysłałeś wiadomość o następującej treści:\n\n" + tresc,
				  od,
				  [mailZwrotny],
				  fail_silently=False)
		return HttpResponse('Wysłano wiadomości')


##########################################################################################
#ANDROID
##########################################################################################


# Android - Dodanie wiadomosci z shoutboxa do bazy danych
def dodajWShoutboxieAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			wiadomosc = request.POST['message']
			if wiadomosc != "":
				shout = models.Shoutbox(student = student,
										tresc = wiadomosc,
										data = datetime.datetime.now(),
										czyWazne = False)
				shout.save()
				return shoutboxAND(request)
		else:
			return HttpResponse('-4')
	return HttpResponse("Fail")

# Android - wyświetlenie wiadomości z shoutboxa
def shoutboxAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			stopien = student.rodzajStudiow
			semestr = student.semestr
			kierunek = student.kierunek
			shoutbox = models.Shoutbox.objects.filter(student__kierunek = kierunek,
													  student__rodzajStudiow = stopien,
													  student__semestr = semestr).order_by('data')[:10]
			shoutbox = shoutbox.reverse()
	
			idSt = shoutbox.values_list('student_id', flat = True)
			studenci = models.Student.objects.filter(id__in = idSt)
			idUzShoutboxa = studenci.values_list('uzytkownik_id', flat=True)
			uz = models.Uzytkownik.objects.filter(id__in = idUzShoutboxa)
			obiekt = list(shoutbox) + list(uz) + list(studenci)
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(obiekt, ensure_ascii=False, fields = ('nick', 'data', 'tresc', 'uzytkownik', 'student'))
			return HttpResponse(wynik, mimetype="application/json")
		else:
			return HttpResponse('-4')
	else:
		return HttpResponse("Fail")

'''
# Android - wyświetlenie wiadomości z shoutboxa
def shoutboxAND(request):
	if post(request):
		student = studPost(request)
		stopien = student.rodzajStudiow
		semestr = student.semestr
		kierunek = student.kierunek
		shoutbox = models.Shoutbox.objects.filter(kierunek = kierunek,
												  rodzajStudiow = stopien,
												  semestr = semestr).order_by('data')[:10]
		shoutbox = shoutbox.reverse()
		idUzShoutboxa = shoutbox.student.values_list('uzytkownik_id', flat=True)
		uz = models.Uzytkownik.objects.filter(id__in = idUzShoutboxa)
		obiekt = list(shoutbox) + list(uz)
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(obiekt, ensure_ascii=False, fields = ('nick', 'data', 'tresc', 'uzytkownik'))
		return HttpResponse(wynik, mimetype="application/json")
	else:
		return HttpResponse("Failed")

'''
# Android - wyswietlenie planu zajec - przeslanie grup
def planAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			grupy = models.Grupa.objects.filter(uzytkownik = uzytkownik).order_by('godzinaOd')
			idWykl = grupy.values_list('prowadzacy_id', flat=True)
			idKurs = grupy.values_list('kurs_id', flat=True)
			wykladowcy = models.Prowadzacy.objects.filter(id__in = idWykl)
			kursy = models.Kurs.objects.filter(id__in = idKurs)
			lista = list(grupy) + list(kursy) + list(wykladowcy)
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(lista, ensure_ascii=False, fields = ('prowadzacy',
																				   'dzienTygodnia',
																				   'parzystosc',
																				   'godzinaOd',
																				   'godzinaDo',
																				   'miejsce',
																				   'kurs',
																				   'nazwisko',
																				   'imie',
																				   'tytul',
																				   'nazwa',
																				   'rodzaj'))
		else:
			return HttpResponse('-4')
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


		
# Android - wyswietlenie zblizajacych sie wydarzen
def mojeWydarzeniaAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			wczoraj = datetime.date.today() - datetime.timedelta(days=1)
			ileWydarzen = uzytkownik.ileMoichWydarzen
			wydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gt = wczoraj).order_by('dataWydarzenia', 'godzinaOd')[:ileWydarzen]
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(wydarzenia, ensure_ascii=False)
			return HttpResponse(wynik, mimetype="application/json")
		else:
			return HttpResponse('-4')
	return HttpResponse("Fail")


# Android - wyswietlenie ostatnio dodanych wydarzen
def ostatnieWydarzeniaAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			wydarzenia = models.Wydarzenie.objects.all()
			wydarzeniaUz = uzytkownik.wydarzenie_set.all()
			# Tutaj trzeba wybrac odpowiednie wydarzenia!!!
			wydarzenia = wydarzenia.exclude(id__in=wydarzeniaUz) 
			wydarzenia = wydarzenia.order_by('-dataDodaniaWyd', '-godzinaOd')[:10]
			idSt = wydarzenia.values_list('dodal_id', flat = True)
			studenci = models.Student.objects.filter(id__in = idSt)
			idUz = studenci.values_list('uzytkownik_id', flat=True)
			uzytkownicy = models.Uzytkownik.objects.filter(id__in = idUz)
			lista = list(wydarzenia) + list(studenci) + list(uzytkownicy)
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(lista, ensure_ascii=False, fields = ('nazwa',
																				   'opis',
																				   'dataWydarzenia',
																				   'godzinaOd',
																				   'godzinaDo',
																				   'dataDodaniaWyd',
																				   'dodal_id',
																				   'uzytkownik',
																				   'nick'))
			return HttpResponse(wynik, mimetype="application/json")
		else:
			return HttpResponse('-4')
	return HttpResponse("Fail")


# Android - wyswietlenie listy wykladowcow, ich konsultacji oraz planu zajec
def listaWykladowcowAND(request):
	wykladowcy = models.Prowadzacy.objects.all().order_by('nazwisko')
	konsultacje = models.Konsultacje.objects.all()
	kategoria = models.KategoriaMiejsca.objects.get(id=1)
	budynki = models.Miejsce.objects.filter(kategoria = kategoria)
	grupy = models.Grupa.objects.all().order_by('godzinaOd')
	kursy = models.Kurs.objects.all()
	wydzialy = models.Wydzial.objects.all()
	lista = list(kursy) + list(wykladowcy) + list(konsultacje) + list(grupy) +list(budynki)
	
	json_serializer = serializers.get_serializer("json")()
	wynik = json_serializer.serialize(lista, ensure_ascii=False)
	return HttpResponse(wynik, mimetype="application/json")


# Android - wyswietlanie wydarzen z kalendarza
def kalendarzAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			wydarzenia = uzytkownik.wydarzenie_set.all().order_by('dataWydarzenia', 'godzinaOd')
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(wydarzenia, ensure_ascii=False)
			return HttpResponse(wynik, mimetype="application/json")
		else:
			return HttpResponse('-4')
	return HttpResponse("Fail")


def logowanieAND(request):
	if post(request):
		nickPost = request.POST['login']
		hasloPost = request.POST['password']
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
							return HttpResponse('-4') # zmiana hasla
						else:
							return HttpResponse(student.id)
					else:
						return HttpResponse('-3') # konto nieaktywne
				else:
					return HttpResponse('-5')
			else:
					return HttpResponse('-2') # bledny login lub haslo
		except:
				return HttpResponse('-2') # bledny login lub haslo
	else:
			return HttpResponse('-1') # blad wyslania


def zmianaHaslaPrzyLogowaniuAND(request):
	if post(request):
		dane = request.POST.copy()
		try:
			uzytkownik = models.Uzytkownik.objects.get(nick = dane['login'])
			print('znalazlo uzytkownika')
		except:
			return HttpResponse('-2') #bledny login lub haslo
		starePasuje = sha256_crypt.verify(dane['oldPass'], uzytkownik.haslo)
		if starePasuje:
			print('stare haslo pasuje')
			hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', dane['newPass'])
			hasloOk = hasloOk and (dane['newPass'] == dane['newPass2'])
			if hasloOk:
				print('nowe haslo spelnia wymagania')
				if not sha256_crypt.verify(dane['newPass'], uzytkownik.haslo):
					uzytkownik.haslo = sha256_crypt.encrypt(dane['newPass'])
					uzytkownik.dataOstZmianyDanych = datetime.date.today()
					uzytkownik.save()
					print('zapisano nowe haslo')
					return HttpResponse('0')
				else:
					return HttpResponse('-6') #nowe haslo nie rozni sie od starego
			else:
				return HttpResponse('-7') # haslo nie spelnia wymagan
		else:
			return HttpResponse('-2') #bledny login lub haslo
		
	else:
		return HttpResponse('-1') #blad wyslania
	

def przeslijAktywatorPonownieAND(request):
	print('Wywolalo')
	if post(request) and 'login' in request.POST.keys():
		print('jest postem')
		nick = request.POST['login']
		try:
			uzytkownik = uz(nick)
			print('pobrano uzytkownika')
			if (uzytkownik.czyAktywowano == False):
				print('nieaktywne')
				uzytkownik.aktywator = wygenerujAktywator()
				print('tu sie nie wywalilo')
				uzytkownik.save()
				print('zapisalo')
				wyslijPotwierdzenie(uzytkownik)
				print('wyslalao potwierdzenie')
			else:
				return HttpResponse('-8') #konto jest aktywne
		except:
			return HttpResponse("-2") #bledny login
	return HttpResponse("0") #wyslano aktywator ponownie

def daneStudentaAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		razemUzytStud = list(student) + list(uzytkownik)
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(razemUzytStud, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


def dodajWydDoKalendarzaAND(request):
	try:
		if post(request):
			uzytkownik = uzPost(request)
			wydarzenie = models.Wydarzenie.objects.get(id = request.POST['idWyd'])
			if (wydarzenie not in uzytkownik.wydarzenie_set.all()):
				kalendarz = models.Kalendarz(uzytkownik = uzytkownik, wydarzenie = wydarzenie, opis = wydarzenie.opis) 
				kalendarz.save()
		return HttpResponse('Ok')     
	except:
		return HttpResponse("Fail")	
	
############################################# TESTOWANIE ###################################



# Klasa do testow
def test(request):
	return render_to_response('index.html', {'strona':'test2', 'logowanie':True})

def test2(request):
	nick = 'ktosik'
	indeks = '899888'
	wydz = models.Wydzial.objects.all()
	return render_to_response('registration.html', {'nick': nick, 'index': indeks, 'wydzialy': wydz})

