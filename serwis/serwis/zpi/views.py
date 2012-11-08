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
			usunSesje(request)
			tekst = 'Musisz zmienić swoje hasło.'
			return render_to_response('index.html', {'strona':'portal', 'logowanie':True, 'blad':True, 'tekstBledu':tekst, 'zmianaHasla':True})
		
		##################################
		# Rejestracja
		# Wyswietlenie rejestracjia
		elif kom == '5':
			#usunSesje(request)
			return render_to_response('index.html', {'strona':'registration', 'logowanie':True})
	else:
		return render_to_response('index.html', {'strona':'portal', 'logowanie':True})

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
	tresc = tresc + "http://127.0.0.1:8000/confirm/" + uzytkownik.aktywator + "/" + uzytkownik.nick.encode('utf-8')
	#send_mail(tytul, tresc, 'pwrtracker@gmail.com', [student.indeks + "@student.pwr.wroc.pl"], fail_silently=False)

	
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
			if(zgodnosc):
				if jestStudentem(uzytkownik):
					domyslny = uzytkownik.domyslny
					student = models.Student.objects.get(id = domyslny)
					if uzytkownik.czyAktywowano:
						if czyZmienicHaslo(uzytkownik):
							request.session['komunikat'] = '4' # zmiana hasla
						else:
							request.session['studentId'] = student.id
							request.session['content'] = 'news'
					else:
						request.session['komunikat'] = '3' # konto nieaktywne
				else:
					if czyZmienicHaslo(uzytkownik):
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
	return 0


# Przeslanie aktywatora ponownie - wygenerowanie nowego
def przeslijAktywatorPonownie(request):
	if post(request) & 'fld_login' in request.POST.keys():
		nick = request.POST['fld_login']
		try:
			uzytkownik = uz(nick)
			if (uzytkownik.czyAktywowano == False):
				uzytkownik.aktywator = wygenerujAktywator()
				uzytkownik.save()
				wyslijPotwierdzenie(uzytkownik)
			else:
				return HttpResponse("Twoje konto jest już aktywne")
		except:
			return HttpResponse("Nie ma takiego uzytkownika")
	return HttpResponse("Wysłano aktywator ponownie")
	

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
	wydarzenia = models.Wydarzenie.objects.all()
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
	response.write('</i>')
	return response



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

# Zaladowanie strony account.html do diva na stronie glownej
def zaladujKonto(request):
	student = studSesja(request)
	uzytkownik = student.uzytkownik
	studenci = models.Student.objects.filter(uzytkownik = uzytkownik)
	return render_to_response('account.html', {'studenci':studenci, 'uzytkownik':uzytkownik})



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
		wiadomosc = request.POST['message']
		if wiadomosc != "":
			shout = models.Shoutbox(student = student,
									tresc = wiadomosc,
									data = datetime.datetime.now(),
									czyWazne = False)
			shout.save()
			return shoutboxAND(request)
	return HttpResponse("Failed")

# Android - wyświetlenie wiadomości z shoutboxa
def shoutboxAND(request):
	if post(request):
		student = studPost(request)
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
		return HttpResponse("Failed")

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
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


		
# Android - wyswietlenie zblizajacych sie wydarzen
def mojeWydarzeniaAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		wczoraj = datetime.date.today() - datetime.timedelta(days=1)
		ileWydarzen = uzytkownik.ileMoichWydarzen
		wydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gt = wczoraj).order_by('dataWydarzenia', 'godzinaOd')[:ileWydarzen]
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(wydarzenia, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


# Android - wyswietlenie ostatnio dodanych wydarzen
def ostatnieWydarzeniaAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
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
	return HttpResponse("Fail")


# Android - wyswietlenie listy wykladowcow, ich konsultacji oraz planu zajec
def listaWykladowcowAND(request):
	if post(request):
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
	return HttpResponse("Fail")


# Android - wyswietlanie wydarzen z kalendarza
def kalendarzAND(request):
    if post(request):
        student = studPost(request)
        uzytkownik = student.uzytkownik
        wydarzenia = uzytkownik.wydarzenie_set.all().order_by('dataWydarzenia', 'godzinaOd')
        json_serializer = serializers.get_serializer("json")()
        wynik = json_serializer.serialize(wydarzenia, ensure_ascii=False)
        return HttpResponse(wynik, mimetype="application/json")
    return HttpResponse("Fail")


'''
# Android - wyswietlenie konsultacji wykladowcow
def konsultacjeWykladowcowAND(request):
	if post(request):
		konsultacje = models.Konsultacje.objects.all()
		json_serializer = serializers.get_serializer("json")()
		wynik = json_serializer.serialize(konsultacje, ensure_ascii=False)
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


# Android - wyswietlenie planów wykladowcow
def planyWykladowcowAND(request):
	if post(request):
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

'''



############################################# TESTOWANIE ###################################



# Klasa do testow
def test(request):
	if True:
		student = models.Student.objects.get(id = 9)
		uzytkownik = student.uzytkownik
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
		return HttpResponse(wynik, mimetype="application/json")
	return HttpResponse("Fail")


