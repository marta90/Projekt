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


# Wyswietlenie strony glownej
def glowna(request):
	if jestSesja(request):
		nick = request.session['nick']
		if 'content' not in request.session.keys():
			request.session['content'] = 'news'
		return render_to_response('index.html', {'strona':'news', 'nick':nick, 'wyloguj':"wyloguj"}) #DODAC WYSWIETLANIE ZALOGOWANEGO UZYTKOWNIKA
	else:
		return render_to_response('index.html', {'strona':'portal', 'logowanie':True}) #TU MA BYC NA STRONIE MENU Z LOGOWANIEM

def dodajShout(request, wiadomosc):
	#u = models.Uzytkownik.objects.get(nick = request.session['nick'])
	u = models.Uzytkownik.objects.get(nick = 'nick1')
	if wiadomosc != "":
		s = models.Shoutbox(uzytkownik = u, tresc = wiadomosc, data = datetime.datetime.now(), czyWazne = False)
		s.save()
	return HttpResponseRedirect("/media/html/news.html")

# Sprawdzenie czy sesja jest otwarta
def jestSesja(request):
	return ('nick' in request.session) & ('idUz' in request.session)

# Wyswietlenie rejestracji
def rejestruj(request):
	if request.method == 'POST':
		nick = request.POST['fld_loginCheck']
		indeks = request.POST['fld_indexNumber']
		wydz = models.Wydzial.objects.all()
		return render_to_response('registration.html', {'nick': nick, 'index': indeks, 'wydzialy': wydz})
	else:
		return HttpResponse("Nie sprawdzono poprawności loginu oraz numer indeksu.")

# Rejestracja użytkownika
@transaction.commit_on_success
def zarejestruj(request):
	if request.method == 'POST':
		nick = 'fld_nick' in request.POST.keys()
		indeks = 'fld_index' in request.POST.keys()
		haslo = 'fld_pass' in request.POST.keys()
		haslo2 = 'fld_passRepeat' in request.POST.keys()
		imie = 'fld_name' in request.POST.keys()
		nazwisko = 'fld_lastName' in request.POST.keys()
		semestr = 'select_semester' in request.POST.keys()
		kierunek = 'select_faculty' in request.POST.keys()
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
			kierunek = request.POST['select_faculty']
			stopienStudiow = request.POST['select_type']
			poprawnosc = sprawdzDane(nick, imie, nazwisko, indeks, haslo, haslo2, semestr, kierunek, stopienStudiow)
			if(poprawnosc):
				kierunek = models.Kierunek.objects.get(id = request.POST['select_faculty'])
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

# Klasa do testow
def test(request):
	if True:
		indeks = '121212'
		try:
			student = models.Student.objects.get(indeks = indeks)
			if (student.czyAktywowano == False):
				student.aktywator = wygenerujAktywator()
				student.save()
				wyslijPotwierdzenie(student)
			else:
				return HttpResponse("Twoje konto jest już aktywne")
		except:
			return HttpResponse("Nie ma takiego uzytkownika")
	return HttpResponse("Fail")

def przeslijAktywatorPonownie():
	if request.method == 'POST' & 'fld_index' in request.POST.keys():
		indeks = request.POST['fld_index']
		try:
			student = models.Student.objects.get(indeks = indeks)
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
	st = models.Student.objects.filter(indeks=indeks)
	if st.exists():
		student = models.Student.objects.get(indeks=indeks)
		if student.aktywator == aktywator:
			student.czyAktywowano = True
			student.save()
			return HttpResponse("Udało się aktywować")
	return HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")		

# Sprawdzenie czy dany uzytkownik jest studentem	
def jestStudentem(uzytkownik):
	st = models.Student.objects.filter(uzytkownik=uzytkownik)
	odp = st.exists()
	return odp

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
def logowanie(request):	 #Dodaj sprawdzanie aktywacje i sprawdzanie hasla > 30 dni
	if request.method == 'POST':
		zlyLogin = 'Podany login i/lub hasło są nieprawidłowe.'
		bladWyslania = 'Wystąpił błąd. Spróbuj ponownie.'
		zmienHaslo = 'Coś ze zmianą hasła'
		nickPost = request.POST['fld_login']
		hasloPost = request.POST['fld_pass']
		uz = models.Uzytkownik.objects.filter(nick=nickPost)
		if uz.exists():
			uzytkownik = models.Uzytkownik.objects.get(nick=nickPost)
			haslo = uzytkownik.haslo
			zgodnosc = sha256_crypt.verify(hasloPost, haslo)
			if(zgodnosc):
				if jestStudentem(uzytkownik):
					student = models.Student.objects.get(uzytkownik=uzytkownik)
					if student.czyAktywowano:
						if czyZmienicHaslo(uzytkownik):
							return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu': zmienHaslo, 'zmianaHasla': True})
						else:
							request.session['nick'] = nickPost # SESJA
							request.session['idUz'] = models.Uzytkownik.objects.get(nick=nickPost).id # SESJA
							request.session['content'] = 'news'
							return HttpResponseRedirect('/')
					else:
						return HttpResponse('Musisz aktywować konto, aby móc się zalogować. Jeśli chcesz wysłać aktywator jeszcze raz kliknij w poniższy link')
				else:
					if czyZmienicHaslo(uzytkownik):
						return HttpResponse('Trzeba zmienić hasło')
					else:
						request.session['nick'] = nickPost # SESJA
						request.session['idUz'] = models.Uzytkownik.objects.get(nick=nickPost).id # SESJA
						request.session['content'] = 'news'
						return HttpResponseRedirect('/')
			else:
					return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':zlyLogin})
		else:
				return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':zlyLogin})
				#return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu': zmienHaslo, 'zmianaHasla': True})
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
	ok = len(nick)>=2
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
		#odp = odp + 'obj.options[obj.options.length] = new Option(\''+ k.nazwa +'\' , \'' + str(k.id) + '\'); '
		odp = odp + '<option value=\'' + str(k.id) +'\'>' + k.nazwa + '</option>'
	return HttpResponse(odp)

#Pobieranie Semestrów dla poszczególnych kierunków i typu studiów. Potrzebne przy rejestracji
def pobierzSemestry(request, idSpec, idTyp):
	k = models.Kierunek.objects.get(id=idSpec)
	odp = ""
	if idTyp == "1":
		for i in range(1, k.liczbaSemestrow1st + 1):
			odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
	if idTyp == "2":
		for i in range(1, k.liczbaSemestrow2stPoInz + 1):
			odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
	return HttpResponse(odp)

# Zaladowanie strony portal.html do diva na stronie glownej
def zaladujPortal(request):
	if jestSesja(request):
		return zaladujNewsy(request)
	else:
		return render_to_response('portal.html')

def zaladujNewsy(request):
	shoutbox = models.Shoutbox.objects.all().order_by('data')[:10]
	shoutbox = shoutbox.reverse
	#uzytkownik = models.Uzytkownik.objects.get(nick = request.session['nick'])
	u = models.Uzytkownik.objects.get(nick = 'nick1')
	return render_to_response('news.html', {'rozmowy':shoutbox ,'uz':u})

# Zaladowanie strony timetable.html do diva na stronie glownej
def zaladujPlan(request):
	if jestSesja(request):
		st = models.Student.objects.get(uzytkownik = request.session['idUz'])
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
	return render_to_response('teachers.html')

# Zaladowanie strony map.html do diva na stronie glownej
def zaladujMape(request):
	return render_to_response('map.html')

# Zaladowanie strony account.html do diva na stronie glownej
def zaladujKonto(request):
	return render_to_response('account.html')

# Wysyłanie maila do admina
def wyslijEmail(request):
	if request.method == 'POST':
		do = "179298@student.pwr.wroc.pl"
		od = "179298@student.pwr.wroc.pl"
		mailZwrotny = request.POST['fld_email'].encode('utf-8')
		tytul = request.POST['fld_topic'].encode('utf-8')
		tresc = request.POST['fld_text'].encode('utf-8')
		send_mail(tytul, tresc+ "\n\nWiadomość wysłana od\n" + mailZwrotny, od, [do], fail_silently=False)
		send_mail("PwrTracker - wysłano wiadomość: " + tytul, "Wysłałeś wiadomość o następującej treści:\n\n" + tresc, od, [mailZwrotny], fail_silently=False)
		return HttpResponse('Wysłano wiadomości')

#############################################
#ANDROID
#############################################



# Android - Dodanie wiadomosci z shoutboxa do bazy danych
def dodajWShoutboxieAND(request):
	if request.method == 'POST':
		nick = request.POST['nick']
		wiadomosc = request.POST['message']
		uzytkownik = models.Uzytkownik.objects.get(nick = nick)
		if wiadomosc != "":
			shout = models.Shoutbox(uzytkownik = uzytkownik, tresc = wiadomosc, data = datetime.datetime.now())
			shout.save()
			return HttpResponse("Zapisalo")
	return HttpResponse("Nie zapisało")

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











