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

# Czy tydzien jest parzysty
def czyParzystyTydzien(data):          
    if (int(data.strftime("%W")) % 2 == 0):
        return True
    else:
        return False
    
# Funkcja sprawdzajace dopasowanie tekstu do wzorca
def pasuje(wzorzec, tekst):
    if (re.match(wzorzec, tekst)):
            return True
    else:
            return False
        
# Wysyłanie maila do admina
def wyslijEmail(request):
	try:
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
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')
	
# Do zmiany hasła - czy stare hasło się zgadza oraz czy nowe spełnia ograniczenia
def sprHasloZeStarym(haslo, haslo2, stareHaslo, hasloUz):
	hasloOk = pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', haslo)
	hasloOk = hasloOk and (haslo == haslo2)
	hasloOk = hasloOk and sha256_crypt.verify(stareHaslo, hasloUz)
	return hasloOk

# Czy liczba wydarzen sie zgadza
def sprWydarzenia(ileWydarzen):
	wydarzeniaOk = (ileWydarzen == '0' or ileWydarzen == '1' or ileWydarzen == '3' or ileWydarzen == '7' or ileWydarzen == '14' or ileWydarzen == '28')
	return wydarzeniaOk

# Czy semestr sie zgadza
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

# Czy imie spełnia ograniczenia
def sprImie(imie):
	imieOk = pasuje("^([a-zA-Z '-]+)$", imie)
	return imieOk and len(imie)>=2

# Czy nazwisko spełni ograniczenia
def sprNazwisko(nazwisko):
	nazwiskoOk = pasuje("^([a-zA-Z '-]+)$", nazwisko)
	return nazwiskoOk and len(nazwisko)>=2

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

# Filtrowanie wydarzeń	
def filtrujNoweWydarzenia(st):
	student = st
	uzytkownik = student.uzytkownik
	kierStudenta = student.kierunek
	wydzStudenta = student.kierunek.wydzial
	semStudenta = student.semestr
	rodzStudenta = student.rodzajStudiow
	wydarzenia = models.Wydarzenie.objects.filter((Q(dodal__kierunek = kierStudenta) & Q(rodzajWydarzenia = 3)) | (Q(dodal__kierunek__wydzial = wydzStudenta) & Q(rodzajWydarzenia = 2)) |
													(Q(rodzajWydarzenia = 1)) | (Q(grupa__uzytkownik = uzytkownik) & Q(rodzajWydarzenia = 4)) |
													(Q(dodal__semestr = semStudenta) & Q(dodal__rodzajStudiow = rodzStudenta) & Q(dodal__kierunek = kierStudenta)& Q(rodzajWydarzenia = 5)) )
	return wydarzenia

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
	tresc = tresc + "http://" + adresSerwera + "/confirm/" + uzytkownik.aktywator + "/" + uzytkownik.nick.encode('utf-8')
	tresc = tresc + "\n\nJeśli nie zakładałeś konta na PwrTracker możesz przerwać proces rejestracji klikając w ten link:\n"
	tresc = tresc + "http://" + adresSerwera + "/remove/" + uzytkownik.aktywator + "/" + uzytkownik.nick.encode('utf-8')
	send_mail(tytul, tresc, 'pwrtracker@gmail.com', [uzytkownik.mail], fail_silently=False)

# Czy nazwa wydarzenia spełnia ograniczenia
def sprNazweWyd(nazwa):
	if len(nazwa) >0 and len(nazwa)<51:
		return True
	else:
		return False

# Czy opis wydarzenia spełnia ograniczenia	
def sprOpisWyd(opis):
	if len(opis) >0 and len(opis)<251:
		return True
	else:
		return False

# Czy zmienna jest godziną	
def sprGodzine(godzina):
	integer = pasuje('\d+', godzina)
	if integer and int(godzina)>=0 and int(godzina) <24:
		return True
	else:
		return False

# Czy zmienna jest minutą
def sprMinute(minuta):
	integer = pasuje('\d+', minuta)
	if integer and int(minuta)>=0 and int(minuta) <60:
		return True
	else:
		return False
	
# Czy wydarzenie ma odpowiedni rodzaj
def sprRodzaj(rodzaj):
	if rodzaj == "1" or rodzaj == "2" or rodzaj == "3" or rodzaj == "4" or rodzaj == "5" or rodzaj == "6":
		return True
	else:
		return False

# Czy grupa jest w planie uzytkownika	
def sprGrupe(grupa, uzytkownik):
	try:
		print('Id grupy ' + grupa)
		grupa = models.Grupa.objects.get(id = int(grupa))
		if grupa in uzytkownik.grupa_set.all():
			return True
		else:
			print('grupa nie jest w planie uzytkownika')
			return False
	except:
		print('nie ma takiej grupy')
		return False

# Czy istnieje taka data
def sprDate(dzien, miesiac, rok):
	try:
		data = datetime.date(int(rok), int(miesiac), int(dzien))
		return True
	except:
		return False
	
# Usuwanie sesji	
def usunSesje(request):
	try:
		for elemSesji in request.session.keys():
			del request.session[elemSesji]
	except KeyError:
		pass
	
def kontakt(request):
	admini = models.Student.objects.filter(uprawnienia = 1).order_by('kierunek', 'uzytkownik__nick')
	return render_to_response('contact.html', {'admini':admini})

'''
def saWPoscie(request, dane):
	for d in dane:
		if d not in request.POST.keys():
			return False
		else:
			return True
''' 