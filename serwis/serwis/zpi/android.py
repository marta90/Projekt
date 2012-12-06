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
			wynik = json_serializer.serialize(obiekt, ensure_ascii=False, fields = ('nick', 'data', 'tresc', 'uzytkownik', 'student', 'czyWazne'))
			return HttpResponse(wynik, mimetype="application/json")
		else:
			return HttpResponse('-4')
	else:
		return HttpResponse("Fail")


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
			tygodnie = models.Tydzien.objects.all()
			zmianyDat = models.Tydzien.objects.all()
			lista = list(grupy) + list(kursy) + list(wykladowcy) + list(tygodnie) + list(zmianyDat)
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
																				   'rodzaj',
																				   'nrTygodnia',
																				   'dataOd',
																				   'dataDo',
																				   'rokAkademicki',
																				   'semestr',
																				   'data',
																				   'tydzien',
																				   'nowyDzien'))
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
			dataMin = datetime.date.today()
			ileWydarzen = uzytkownik.ileMoichWydarzen
			dataMax = dataMin + datetime.timedelta(days = ileWydarzen+1)
			mojeWydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gte = dataMin, dataWydarzenia__lte = dataMax).order_by('dataWydarzenia', 'godzinaOd')
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(mojeWydarzenia, ensure_ascii=False)
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
			wydarzenia = filtrujNoweWydarzenia(student) #zwraca wydarzenia odpowiednie tylko dla wybranego uzytkownika
			wydarzeniaUz = uzytkownik.wydarzenie_set.all() #zbior wydarzen znajdujacych sie w kalendarzu uzytkownika
			wydarzenia = wydarzenia.exclude(id__in=wydarzeniaUz) #pokazanie tylko tych wydarzen, ktorych nie ma w kalendarzu uzytkownika
			wydarzenia = wydarzenia.filter(dataWydarzenia__gte = datetime.date.today())
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


	# Zmiana opisu wydrzenia
def zmienOpisAND(request):
	try:
		idWyd = request.POST['evId']
		print('1')
		opis = request.POST['description']
		print('2')
		student = studPost(request)
		print('3')
		uzytkownik = student.uzytkownik
		print('4')
		kalendarz = models.Kalendarz.objects.get(uzytkownik = uzytkownik, wydarzenie_id = idWyd)
		print('5')
		kalendarz.opis = opis
		print('6')
		kalendarz.save()
		print('7')
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')


def oznaczWaznyShoutAND(request):
	try:
		for k in request.POST.keys():
			print k
		idSh = request.POST['shoutId']
		print(idSh)
		student = studPost(request)
		print(student.indeks)
		uzytkownik = student.uzytkownik
		shout = models.Shoutbox.objects.get(id = idSh)
		print('pobralo')
		shout.czyWazne = True
		print('ustawilo na true')
		shout.save()
		print('zapisalo')
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')

def oznaczNiewaznyShoutAND(request):
	try:
		idSh = request.POST['shoutId']
		student = studPost(request)
		uzytkownik = student.uzytkownik
		shout = models.Shoutbox.objects.get(id = idSh)
	except:
		return HttpResponse('Fail')
	if shout.student == student:
		shout.czyWazne = False
		shout.save()
		return HttpResponse('Ok')
	else:
		return HttpResponse('Forbidden')
		
		
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
	wynik = json_serializer.serialize(lista, ensure_ascii=False, fields = ('id',
																		   'nazwa',
																		   'rodzaj',
																		   'nazwisko',
																		   'imie',
																		   'tytul',
																		   'konflikt',
																		   'prowadzacy',
																		   'dzienTygodnia',
																		   'parzystosc',
																		   'godzinaOd',
																		   'godzinaDo',
																		   'budynek',
																		   'sala',
																		   'inneInformacje',
																		   'miejsce',
																		   'kurs'))
	return HttpResponse(wynik, mimetype="application/json")


# Android - wyswietlanie wydarzen z kalendarza
def kalendarzAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			wydarzenia = uzytkownik.wydarzenie_set.all().order_by('dataWydarzenia', 'godzinaOd')
			kalendarz = models.Kalendarz.objects.filter(uzytkownik = uzytkownik)
			lista = list(wydarzenia) + list(kalendarz)
			json_serializer = serializers.get_serializer("json")()
			wynik = json_serializer.serialize(lista, ensure_ascii=False)
			return HttpResponse(wynik, mimetype="application/json")
		else:
			return HttpResponse('-4')
	return HttpResponse("Fail")


#Logowanie na Androidzie
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
					return HttpResponse('-5') # uzytkownik nie jest studentem
			else:
					return HttpResponse('-2') # bledny login lub haslo
		except:
				return HttpResponse('-2') # bledny login lub haslo
	else:
			return HttpResponse('-1') # blad wyslania


# Zmiana hasla przy logowaniu (wymuszona - mineło ponad 30 dni)
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
					uzytkownik.dataOstZmianyHasla = datetime.date.today()
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
	

# Ponowne wysłanie akrtywatora
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


# Wysłanie danych studenta
def daneStudentaAND(request):
	if post(request):
		student = studPost(request)
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


# Dodawanie gotowych wydarzen do kalendarza
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
	

def zaladujWazneWiadomosciAND(request):
	if post(request):
		student = studPost(request)
		uzytkownik = student.uzytkownik
		if not czyZmienicHaslo(uzytkownik):
			stopien = student.rodzajStudiow
			semestr = student.semestr
			kierunek = student.kierunek
			shoutbox = models.Shoutbox.objects.filter(student__kierunek = kierunek,
													  student__rodzajStudiow = stopien,
													  student__semestr = semestr,
													  czyWazne = True).order_by('data')[:10]
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


# Dodawanie wydarzen z kodu QR
def dodajZQrAND(request):
	try:
		if post(request):
			uzytkownik = uzPost(request)
			wydarzenie = models.Wydarzenie.objects.get(id = request.POST['idWyd'])
			if (wydarzenie not in uzytkownik.wydarzenie_set.all()):
				kalendarz = models.Kalendarz(uzytkownik = uzytkownik, wydarzenie = wydarzenie, opis = wydarzenie.opis) 
				kalendarz.save()
				return HttpResponse('0') # poprawnie zapisano
			else:
				return HttpResponse('-9')# wydarzenie jest juz w kalendarzu  
		return HttpResponse('-5') # inny blad 
	except:
		return HttpResponse('-5') #inny blad


# Usuwanie wydarzenie z kalendarza
def usunWydarzenieAND(request):
	try:
		idWyd = request.POST['evId']
		uzytkownik = uzPost(request)
		kalendarz = models.Kalendarz.objects.get(uzytkownik = uzytkownik, wydarzenie_id = idWyd)
		kalendarz.delete()
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')
	
# Przeslanie informacji o wydarzeniu na podstawie id wydarzenia pobranego z kodu QR	
def qrAND(request, idWyd):
	wydarzenie = models.Wydarzenie.objects.filter(id = idWyd)
	json_serializer = serializers.get_serializer("json")()
	wynik = json_serializer.serialize(wydarzenie, ensure_ascii=False, fields = ('nazwa', 'opis', 'dataWydarzenia', 'godzinaOd', 'godzinaDo'))
	return HttpResponse(wynik, mimetype="application/json")

def mapaAND(request):
	miejsca = models.Miejsce.objects.all()
	kategorie = models.KategoriaMiejsca.objects.all()
	lista = list(miejsca) + list(kategorie)
	json_serializer = serializers.get_serializer("json")()
	wynik = json_serializer.serialize(lista, ensure_ascii=False)
	return HttpResponse(wynik, mimetype="application/json")
	
# Tworzenie nowego wydarzenia
def dodajWydarzenieAND(request):
	if post(request):
		dane = request.POST.copy()
		student = studPost(request)
		uzytkownik = student.uzytkownik
		print('start')
		nazwa = dane['name']
		opis = dane['description']
		godzinaOd = dane['startH']
		minutaOd = dane['startM']
		godzinaDo = dane['endH']
		minutaDo = dane['endM']
		rodzaj = dane['type']
		grupaId = dane['class']
		dzien = dane['day']
		miesiac = dane['month']
		rok = dane['year']
		
		print('pobralo dane')
		if not sprNazweWyd(nazwa):
			print("zla nazwa")
			return HttpResponse('Fail')
		else:
			print('nazwa ok')
		
		if not sprOpisWyd(opis):
			print("zly opis")
			return HttpResponse('Fail')
		else:
			print('opis ok')
		
		if not sprGodzine(godzinaOd):
			print("zla godzinaOd")
			return HttpResponse('Fail')
		else:
			print('godzinaod ok')
		
		if not sprGodzine(godzinaDo):
			print("zla godzinaDo")
			return HttpResponse('Fail')
		else:
			print('godzinado ok')
		
		if not sprMinute(minutaOd):
			print("zla minutaOd")
			return HttpResponse('Fail')
		else:
			print('minutaod ok')
		
		if not sprMinute(minutaDo):
			print("zla minutaDo")
			return HttpResponse('Fail')
		else:
			print('minutado ok')
			
		if not sprRodzaj(rodzaj):
			print("zly rodzaj")
			return HttpResponse('Fail')
		else:
			print('rodzajok')
		
		if grupaId <> "0":
			if not sprGrupe(grupaId, uzytkownik):
				print("zla grupa")
				return HttpResponse('Fail')
		else:
			grupaId = None
		
		
		if not sprDate(dzien, miesiac, rok):
			print("zla data")
			return HttpResponse('Fail')
		
		print('wszystko niby ok')
		dataWyd = datetime.date(int(rok), int(miesiac), int(dzien))
		dataDodaniaWyd = datetime.date.today()
		od = datetime.time(int(godzinaOd), int(minutaOd))
		do = datetime.time(int(godzinaDo), int(minutaDo))
		print('zaraz utworzy sie wydarzenieee')
		wydarzenie = models.Wydarzenie(nazwa = nazwa,
									   opis = opis,
									   dataWydarzenia = dataWyd,
									   godzinaOd = od,
									   godzinaDo = do,
									   dataDodaniaWyd = dataDodaniaWyd,
									   rodzajWydarzenia = int(rodzaj),
									   grupa_id = grupaId,
									   dodal_id = student.id)
		wydarzenie.save()
		
		print(dane['add'])
		if dane['add'] == 'yes':
			print('dodaje do kalnedarza')
			kalendarz = models.Kalendarz(uzytkownik = uzytkownik, wydarzenie = wydarzenie, opis = opis)
			kalendarz.save()
		
		return HttpResponse('Ok')
	else:
		return HttpResponse('Fail')
	
