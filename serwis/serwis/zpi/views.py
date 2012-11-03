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


# Wyswietlenie strony glownej
def glowna(request):
	if jestSesja(request):
		nick = request.session['nick']
		if 'content' not in request.session.keys():
			request.session['content'] = 'news'
		return render_to_response('index.html', {'strona':'news', 'nick':nick, 'wyloguj':"wyloguj"})
	else:
		return render_to_response('index.html', {'strona':'portal', 'logowanie':True})

def uz(nick):
	return models.Uzytkownik.objects.get(nick=nick)

def uzSesja(request):
	return models.Uzytkownik.objects.get(nick=request.session['nick'])

def kier(idK):
	return models.Kierunek.objects.get(id = idK)

def kierSesja(request):
	return models.Kierunek.objects.get(id = request.session['spec'])

def stud(indeks):
	return models.Student.objects.get(indeks = indeks)

def studSesja(request):
	uzytkownik = uzSesja(request)
	return models.Student.objects.get(uzytkownik = uzytkownik)

def post(request):
	if request.method == 'POST':
		return True
	else:
		return False

# Dodanie wiadomosci do shoutboxa
def dodajShout(request, wiadomosc):
	uzytkownik = uzSesja(request)
	kierunek = kierSesja(request)
	stopien = request.session['type']
	semestr = request.session['semester']
	if wiadomosc != "":
		shout = models.Shoutbox(uzytkownik = uzytkownik,
								tresc = wiadomosc,
								data = datetime.datetime.now(),
								czyWazne = False,
								kierunek = kierunek,
								rodzajStudiow = stopien,
								semestr = semestr)
		shout.save()
	return HttpResponseRedirect("/media/html/shoutbox.html")


def konsultacjeWykladowcy(request, idw):
	prowadzacy = models.Prowadzacy.objects.get(id = idw)
	konsultacje = models.Konsultacje.objects.filter(prowadzacy = prowadzacy)
	response = HttpResponse()
	response.write("<i>")
	if konsultacje.exists():
		for k in konsultacje:
			response.write(k.dzienTygodnia)
			if (k.parzystosc == 'TP') or (k.parzystosc == 'TN'):
				response.write(" " + k.parzystosc)
			response.write(" " + k.godzinaOd.strftime("%H:%M") + " - " + k.godzinaDo.strftime("%H:%M") + ", bud. ")
			response.write(k.budynek.nazwa + ", s. " + k.sala + "<br>")
	else:
		response.write('Brak informacji o konsultacjach')
	response.write("</i>")
	return response

# Sprawdzenie czy sesja jest otwarta
def jestSesja(request):
	return ('nick' in request.session)

# Wyswietlenie rejestracji
def rejestruj(request):
	if post(request):
		nick = request.POST['fld_loginCheck']
		indeks = request.POST['fld_indexNumber']
		wydz = models.Wydzial.objects.all()
		return render_to_response('registration.html', {'nick': nick, 'index': indeks, 'wydzialy': wydz})
	else:
		return HttpResponse("Nie sprawdzono poprawności loginu oraz numer indeksu.")

# Rejestracja użytkownika
@transaction.commit_on_success
def zarejestruj(request):
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
				uzytkownik.save()
				uzytkownik.ktoWprowadzil = models.Uzytkownik.objects.get(id = uzytkownik.id)
				uzytkownik.ktoZmienilDane = models.Uzytkownik.objects.get(id = uzytkownik.id)
				uzytkownik.dataOstLogowania = datetime.date.today()
				uzytkownik.dataOstZmianyHasla = datetime.date.today()
				uzytkownik.dataOstZmianyDanych = datetime.date.today()
				uzytkownik.save()
				student = models.Student(uzytkownik = models.Uzytkownik.objects.get(id = uzytkownik.id), indeks = indeks)
				student.save()
				student.aktywator = wygenerujAktywator()
				student.save()
				kierunki = models.KierunkiStudenta(student = student, kierunek = kierunek, rodzajStudiow = stopienStudiow, semestr = semestr)
				kierunki.save()
				wyslijPotwierdzenie(student)
				return render_to_response('index.html', {'alert': "Na Twojego maila studenckiego został wysłany link z aktywacją konta."})
			else:
				return HttpResponse("Dane nie spełniają wymaganych ograniczeń")
		else:
			return HttpResponse("Nie przeslano wszystkich danych")
	else:
		return HttpResponse("Blad danych - spróbuj jeszcze raz")

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




def przeslijAktywatorPonownie(request):
	if post(request) & 'fld_index' in request.POST.keys():
		indeks = request.POST['fld_index']
		try:
			student = stud(indeks)
			if (student.czyAktywowano == False):
				student.aktywator = wygenerujAktywator()
				student.save()
				wyslijPotwierdzenie(student)
			else:
				return HttpResponse("Twoje konto jest już aktywne")
		except:
			return HttpResponse("Nie ma takiego uzytkownika")
	return HttpResponse("Wysłano aktywator ponownie")
	
# Generacja kodu do aktywacji konta
def wygenerujAktywator():
	allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
	import random
	random = random.SystemRandom()
	return ''.join([random.choice(allowed_chars) for i in range(33)])

# Funkcja do oprogramowania
# Przypomnienie hasla
def przypomnijHaslo(request):
	return 0

# Wyslanie maila z kodem potwierdzajacym rejestracje
def wyslijPotwierdzenie(student):
	tytul = "PwrTracker - potwierdzenie rejestracji"
	tresc = "Witaj na PwrTracker!\n\nAby potwierdzić rejestrację w serwisie kliknij na poniższy link.\n"
	tresc = tresc + "http://127.0.0.1:8000/confirm/" + student.aktywator + "/" + student.indeks.encode('utf-8')
	#send_mail(tytul, tresc, 'pwrtracker@gmail.com', [student.indeks + "@student.pwr.wroc.pl"], fail_silently=False)
	
# Potwierdzenie rejestracji po kliknieciu w link aktywacyjny
def potwierdzRejestracje(request, aktywator, indeks):
	try:
		student = stud(indeks)
		if student.aktywator == aktywator:
			student.czyAktywowano = True
			student.save()
			return HttpResponse("Udało się aktywować")
		else:
			HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")	
	except:
		return HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")		

# Sprawdzenie czy dany uzytkownik jest studentem	
def jestStudentem(uzytkownik):
	try:
		student = models.Student.objects.get(uzytkownik=uzytkownik)
		return True
	except:
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


# Logowanie	
def logowanie(request):
	bladWyslania = 'Wystąpił błąd. Spróbuj ponownie.'
	if post(request):
		zlyLogin = 'Podany login i/lub hasło są nieprawidłowe.'
		
		kontoNieaktywne = 'Musisz aktywować konto, aby móc się zalogować. Jeśli chcesz wysłać aktywator jeszcze raz kliknij w poniższy link'
		zmianaHasla = 'Trzeba zmienić hasło'
		
		nickPost = request.POST['fld_login']
		hasloPost = request.POST['fld_pass']
		try:
			uzytkownik = uz(nickPost)
			haslo = uzytkownik.haslo
			zgodnosc = sha256_crypt.verify(hasloPost, haslo)
			if(zgodnosc):
				if jestStudentem(uzytkownik):
					student = models.Student.objects.get(uzytkownik=uzytkownik)
					if student.czyAktywowano:
						if czyZmienicHaslo(uzytkownik):
							return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu': zmienHaslo, 'zmianaHasla': True})
						else:
							try:
								kierunek = student.kierunek.all()[:1].get()
								request.session['spec'] = kierunek.id
								infoOKierunku = models.KierunkiStudenta.objects.get(student = student, kierunek = kierunek)
								request.session['type'] = infoOKierunku.rodzajStudiow
								request.session['semester'] = infoOKierunku.semestr
								request.session['nick'] = nickPost
								request.session['content'] = 'news'
								return HttpResponseRedirect('/')
							except:
								return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':bladWyslania})
					else:
						return HttpResponse(kontoNieaktywne)
				else:
					if czyZmienicHaslo(uzytkownik):
						return HttpResponse(zmianaHasla)
					else:
						request.session['nick'] = nickPost
						request.session['content'] = 'news'
						return HttpResponseRedirect('/')
			else:
					return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':zlyLogin})
		except:
				return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':bladWyslania})
	else:
			return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':bladWyslania})


# Wylogowanie z serwisu - usunięcie sesji
def wylogowanie(request):
	try:
		for elemSesji in request.session.keys():
			del request.session[elemSesji]
	except KeyError:
		pass
	return HttpResponseRedirect('/')

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
	

# Sprawdzanie nicku - dozwolne znaki oraz unikatowość w bazie danych
def sprawdzNick(request, nick):
	if (nickPoprawny(nick) & nickWolny(nick)):
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

# Sprawdzanie indeksu - dozwolne znaki oraz unikatowość w bazie danych
def sprawdzIndeks(request, indeks):
	if (indeksPoprawny(indeks) & indeksWolny(indeks)):
		return HttpResponse('okay')
	else:
		return HttpResponse('denied')
	

def pasuje(wzorzec, tekst):
	if (re.match(wzorzec, tekst)):
		return True
	else:
		return False

#Pobranie kierunków dla okreslonych wydzialow. Potrzebne przy rejestracji
def pobierzKierunki(request, idWydz):
	kierunki = models.Kierunek.objects.filter(wydzial__id=idWydz)
	odp = '<option value=0>Wybierz kierunek...</option>'
	for k in kierunki:
		odp = odp + '<option value=\'' + str(k.id) +'\'>' + str(k.id) + k.nazwa + '</option>'
	return HttpResponse(odp)

#Pobieranie Semestrów dla poszczególnych kierunków i typu studiów. Potrzebne przy rejestracji
def pobierzSemestry(request, idSpec, idTyp):
	kierunek = kier(idSpec)
	odp = ""
	if idTyp == "1":
		for i in range(1, kierunek.liczbaSemestrow1st + 1):
			odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
	if idTyp == "2":
		for i in range(1, kierunek.liczbaSemestrow2stPoInz + 1):
			odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
	return HttpResponse(odp)

# Zaladowanie strony portal.html do diva na stronie glownej
def zaladujPortal(request):
	if jestSesja(request):
		return zaladujNewsy(request)
	else:
		return render_to_response('portal.html')


def zaladujNewsy(request):
	kierunek = kierSesja(request)
	semestr = request.session['semester']
	stopien = request.session['type']
	shoutbox = models.Shoutbox.objects.filter(kierunek = kierunek,
											  semestr = semestr,
											  rodzajStudiow = stopien).order_by('data')[:10]
	shoutbox = shoutbox.reverse()
	uzytkownik = uzSesja(request)
	wczoraj = datetime.date.today() - datetime.timedelta(days=1)
	ileWydarzen = uzytkownik.ileMoichWydarzen
	mojeWydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gt = wczoraj).order_by('dataWydarzenia')[:ileWydarzen]
	wydarzenia = models.Wydarzenie.objects.all()
	wydarzeniaUz = uzytkownik.wydarzenie_set.all()
	wydarzenia = wydarzenia.exclude(id__in=wydarzeniaUz) 
	wydarzenia = wydarzenia.order_by('-dataDodaniaWyd')[:10]
	dzisiaj = datetime.datetime.now()
	wczoraj = dzisiaj - datetime.timedelta(days = 1)
	return render_to_response('news.html', {'rozmowy':shoutbox, 'mojeWydarzenia':mojeWydarzenia, 'wydarzenia':wydarzenia, 'dzisiaj':dzisiaj, 'wczoraj':wczoraj})


def zaladujShoutbox(request):
	kierunek = kierSesja(request)
	semestr = request.session['semester']
	stopien = request.session['type']
	shoutbox = models.Shoutbox.objects.filter(kierunek = kierunek,
											  semestr = semestr,
											  rodzajStudiow = stopien).order_by('data')[:10]
	shoutbox = shoutbox.reverse()
	dzisiaj = datetime.datetime.now()
	wczoraj = dzisiaj - datetime.timedelta(days=1)
	return render_to_response('shoutbox.html', {'rozmowy':shoutbox, 'dzisiaj':dzisiaj, 'wczoraj':wczoraj})


# Zaladowanie strony timetable.html do diva na stronie glownej
def zaladujPlan(request):
	if jestSesja(request):
		st = studSesja(request)
		planPn = models.Plan.objects.filter(student = st.id, grupa__dzienTygodnia = 'pn').order_by('grupa__godzinaOd')
		planWt = models.Plan.objects.filter(student = st.id, grupa__dzienTygodnia = 'wt').order_by('grupa__godzinaOd')
		planSr = models.Plan.objects.filter(student = st.id, grupa__dzienTygodnia = 'śr').order_by('grupa__godzinaOd')
		planCzw = models.Plan.objects.filter(student = st.id, grupa__dzienTygodnia = 'cz').order_by('grupa__godzinaOd')
		planPi = models.Plan.objects.filter(student = st.id, grupa__dzienTygodnia = 'pt').order_by('grupa__godzinaOd')
		czy = True
		if(len(planPn) == 0 and len(planWt) == 0 and len(planSr) == 0 and len(planCzw) == 0 and len(planPi) == 0):
			czy = False
		#return HttpResponse()
		 #and planWt.count==0 and planSr.count==0 and planCzw.count==0 and planPi.count==0
		return render_to_response('timetable.html', {'czyJestPlan':czy, 'pPn':planPn, 'pWt':planWt, 'pSr':planSr, 'pCz':planCzw, 'pPi':planPi})
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")

# Zaladowanie strony calendar.html do diva na stronie glownej
def zaladujKalendarz(request):
	if jestSesja(request):
		return render_to_response('calendar.html')
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")

# Zaladowanie strony teachers.html do diva na stronie glownej
def zaladujWykladowcow(request):
	literaDuza = "A"
	literaMala = literaDuza.lower()
	wykladowcy = models.Prowadzacy.objects.extra(select={'nazwiskoD': 'upper(nazwisko)', 'imieD': 'upper(imie)'}).filter( Q(nazwisko__startswith=literaDuza) | Q(nazwisko__startswith=literaMala)).order_by('nazwiskoD', 'imieD')
	return render_to_response('teachers.html', {'prowadzacy':wykladowcy})

def wykladowcaNaLitere(request, litera):
	literaDuza = litera
	literaMala = litera.lower()

	wykladowcy = models.Prowadzacy.objects.extra(select={'nazwiskoD': 'upper(nazwisko)', 'imieD': 'upper(imie)'}).filter( Q(nazwisko__startswith=literaDuza) | Q(nazwisko__startswith=literaMala)).order_by('nazwiskoD', 'imieD')
	return render_to_response('teachersList.html', {'prowadzacy':wykladowcy})

def znajdzWykladowce(request, nazwa):
	wykladowcy = models.Prowadzacy.objects.extra(select={'nazwiskoD': 'upper(nazwisko)', 'imieD': 'upper(imie)'}).order_by('nazwiskoD', 'imieD')
	wyrazy = nazwa.split()

	calosc = ""
	for i in range(len(wyrazy)):
		wyrazy[i] = usunPolskieZnaki(wyrazy[i]).upper()
		calosc = calosc + wyrazy[i] + " "
	calosc = calosc[:-1]
	#return render_to_response('teachersList.html', {'tekst':wyrazy})
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


def usunPolskieZnaki(text):
	pltoang_tab = {u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ż':'z', u'ź':'z'}
	return ''.join( pltoang_tab.get(char, char) for char in text )


# Zaladowanie strony map.html do diva na stronie glownej
def zaladujMape(request):
	return render_to_response('map.html')

# Zaladowanie strony account.html do diva na stronie glownej
def zaladujKonto(request):
	return render_to_response('account.html')

# Wysyłanie maila do admina
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

#############################################
#ANDROID
#############################################



# Android - Dodanie wiadomosci z shoutboxa do bazy danych
def dodajWShoutboxieAND(request):
	if request.method == 'POST':
		nick = request.POST['nick']
		idKierunku = request.POST['spec']
		stopien = request.POST['type']
		semestr = request.POST['semester']
		wiadomosc = request.POST['message']
		uzytkownik = uz(nick)
		kierunek = kier(idKierunku)
		if wiadomosc != "":
			shout = models.Shoutbox(uzytkownik = uzytkownik,
									tresc = wiadomosc,
									data = datetime.datetime.now(),
									czyWazne = False,
									kierunek = kierunek,
									rodzajStudiow = stopien,
									semestr = semestr)
			shout.save()
			return shoutboxAND(request)
	return HttpResponse("Failed")

# Android - wyświetlenie wiadomości z shoutboxa
def shoutboxAND(request):
	if request.method == 'POST':
		nick = request.POST['nick']
		idKierunku = request.POST['spec']
		stopien = request.POST['type']
		semestr = request.POST['semester']
		kierunek = models.Kierunek.objects.get(id = idKierunku)
		shoutbox = models.Shoutbox.objects.filter(kierunek = kierunek,
												  rodzajStudiow = stopien,
												  semestr = semestr).order_by('data')[:10]
		shoutbox = shoutbox.reverse()
		idUzShoutboxa = shoutbox.values_list('uzytkownik_id', flat=True)
		uz = models.Uzytkownik.objects.filter(id__in = idUzShoutboxa)
		obiekt = list(shoutbox) + list(uz)
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(obiekt, ensure_ascii=False, fields = ('nick', 'data', 'tresc', 'uzytkownik'))
		return HttpResponse(wynik, mimetype="application/json")
	else:
		return HttpResponse("Failed")

# Android - Wyslanie na androida zblizajacych sie wydarzen
def mojeWydarzeniaAND(request):
	if request.method == 'POST':
		nick = request.POST['nick']
		dzisiaj = datetime.date.today() - datetime.timedelta(days=1)
		uzytkownik = models.Uzytkownik.objects.get(nick = nick)
		ileWydarzen = uzytkownik.ileMoichWydarzen
		wydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gt = dzisiaj).order_by('dataWydarzenia')[:ileWydarzen]
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(wydarzenia, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")

# Android - Wyslanie na androida ostatnio dodanych wydarzen
def ostatnieWydarzeniaAND(request):
	if request.method == 'POST':
		nick = request.POST['nick']
		uzytkownik = models.Uzytkownik.objects.get(nick = nick)
		wydarzenia = models.Wydarzenie.objects.all()
		wydarzeniaUz = uzytkownik.wydarzenie_set.all()
		wydarzenia = wydarzenia.exclude(id__in=wydarzeniaUz) 
		wydarzenia = wydarzenia.order_by('-dataDodaniaWyd')[:10]
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(wydarzenia, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")

# Android - Wyslanie na androida listy wykladowcow
def listaWykladowcowAND(request):
	if request.method == 'POST':
		wykladowcy = models.Prowadzacy.objects.all().order_by('nazwisko')
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(wykladowcy, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")

# Android - Wyslanie na androida konsultacji wykladowcow
def konsultacjeWykladowcowAND(request):
	if request.method == 'POST':
		konsultacje = models.Konsultacje.objects.all()
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(konsultacje, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")

# Android - Wyslanie na androida planów wykladowcow
def planyWykladowcowAND(request):
	if request.method == 'POST':
		grupy = models.Grupa.objects.all()
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(grupy, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")

# Android - Wyslanie na androida listy budynków
def budynkiAND(request):
	if request.method == 'POST':
		kategoria = models.KategoriaMiejsca.objects.get(id=1)
		budynki = models.Miejsce.objects.filter(kategoria = kategoria)
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(budynki, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")



# Android - Wyslanie na androida listy budynków
def kursyAND(request):
	if request.method == 'POST':
		kursy = models.Kurs.objects.all()
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(kursy, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")







# Klasa do testow
def test(request):
	uzytkownik = uz('marta')
	return HttpResponse(uzytkownik.nick)
		
		#return HttpResponse(idUzShoutboxa)

def pobierzPlan(request):

    commands.clear_cookies()        # Czyszczenie ciastek
    commands.go("https://edukacja.pwr.wroc.pl/EdukacjaWeb/studia.do")   # Przechodzimy do edukacji
    
    commands.showlinks()            # DO USUNIECIA! Pokazuje linki

    commands.formclear('1')                                 # Czysci formularz logowania
    commands.formvalue('1', 'login', 'pwr84628')            # Podaje login
    commands.formvalue('1', 'password', 'sync53master7')    # Podaje hasło
    commands.submit('0')                                    # Klika zaloguj
    
    print("Linki po submit")                                # DO USUNIECIA! Pokazuje informacje
    commands.showlinks()                                    # DO USUNIECIA! Pokazuje linki
    
    commands.follow("Zapisy")                               # Przechodzi linkiem na stronę zapisów
    
    # DO USUNIECIA! Pokazuje stronę po kliknięciu zapisy!
    print("Co po kliknieciu Zapisy")
    commands.showlinks()
    print "Forms:"
    commands.showforms()

    # Szuka w linkach tego przenoszącego na odpowiedni semestr.
    dateToday = datetime.date.today()
    #dateToday = datetime.date(2012, 6, 10)
    firstOctober = datetime.date(dateToday.year, 10, 1)
    links = commands.showlinks()                            # Pobiera linki z danej strony 

    if dateToday > firstOctober:                            # Jesli dzisiaj jest wiekszy niz 1 Pazdziernika
        #Semestr zimowy
        for link in links:
            ktory = 0
            if link.text=='' + str(dateToday.year) + '/' + str(dateToday.year+1) + '':  # Szukamy linka o tytule (rok/rok+1)
                ktory = ktory + 1
                if ktory == 1:                              # Znalazł!
                    commands.go(link.url)                   # Przechodzimy pod url'sa który się kryje pod tym rokiem
    else:
        #Semest letni
        for link in links:
            ktory = 0
            if link.text=='' + str(dateToday.year)+ '/' + str(dateToday.year+1) + '':   # Szukamy linka o tytule (rok/rok+1)
                ktory = ktory + 1
                if ktory == 2:                              # Znalazł!
                    commands.go(link.url)                   # Przechodzimy pod url'sa który się kryje pod tym rokiem
    
    # DO USUNIECIA! Pokazuje stronę po kliknięciu danego semestru!
    print("Co po kliknieciu semestru:")
    commands.showlinks()
    print "Forms:"
    commands.showforms()
    
    # Szuka w formularzach tego odpowiadającego za pokazanie zapisanych kursów.
    forms = commands.showforms()                            # Pobranie formularzy
    naszForm = None                                         # Zmienna do ktorej zapiszemy znaleziony przez nas form
    for form in forms:                                      # Petla po formualrzach
        if form.action == 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/zapisy.do?href=#hrefZapisySzczSlu':     # Jesli akcja danego formularza przenosi do szczegolow
            naszForm = form                                 # To zapisujemy znaleziony formularz
    
    print(naszForm)                                         # DO USUNIECIA! Wypisuje znaleziony formularz
    
    ctrl = naszForm.controls                                                # pobieram ze znalezionego formularza wszystkie kontrolki
    for ct in ctrl:
        if ct.type == 'submit':                                             # szukam wsrod niej tej co ma typ submit
            commands.get_browser().clicked(naszForm, ct.attrs['name'])      # klikam na ten przycisk
            commands.get_browser().submit()
    
    
    print("Co po kliknieciu szczegoly zajec")
    commands.showlinks()
    print "Forms:"
    commands.showforms()
    
    content = commands.show()
    
    commands.clear_cookies()        #usuwanie ciasteczek
    commands.reset_browser()        #restart przegladarki
    commands.reset_output()
    
    
    return HttpResponse(content)
