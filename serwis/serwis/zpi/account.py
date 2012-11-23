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
# WTF???

def zaladujZmianeHasla(request):
	return render_to_response('changePassword.html')

############### EDYCJA KONTA ##############################################################


# Zaladowanie strony account.html do diva na stronie glownej
def zaladujKonto(request):
	student = studSesja(request)
	uzytkownik = student.uzytkownik
	studenci = models.Student.objects.filter(uzytkownik = uzytkownik, uprawnienia__gte = 0)
	ileKierunkow = studenci.count()
	wydzialy = models.Wydzial.objects.all()
	kierunki = models.Kierunek.objects.all().order_by('nazwa')
	return render_to_response('account.html', {'studenci':studenci, 'uzytkownik':uzytkownik, 'wydzialy':wydzialy, 'ileKierunkow':ileKierunkow, 'kierunki':kierunki})

def usunStudenta(request):
	try:
		print('weszlo')
		uzytkownik = uzSesja(request)
		print('po uz')
		print(request.POST['studentId'])
		student = models.Student.objects.get(id = int(request.POST['studentId']))
		print(student)
		if student.uzytkownik == uzytkownik and uzytkownik.domyslny <> student.id:
			student.uprawnienia = -1
			student.save()
			return HttpResponse('Ok')
		return HttpResponse('Fail')
	except:
		return HttpResponse('Fail')

def zmienDomyslnegoSt(request):
	try:
		print('weszlo')
		uzytkownik = uzSesja(request)
		print('po uz')
		print(request.POST['studentId'])
		student = models.Student.objects.get(id = int(request.POST['studentId']))
		print(student)
		if student.uzytkownik == uzytkownik:
			uzytkownik.domyslny = student.id
			uzytkownik.save()
			return HttpResponse('Ok')
		return HttpResponse('Fail')
	except:
		return HttpResponse('Fail')

# Edycja danych - wywolana ajaxem - zwraca 'Ok' lub 'Fail'
def edytujDane(request):
	if post(request):
		print("---------- Rozpoczyna się edycja danych --------")
		print('W poscie otrzymano nastepujace klucze:')
		uzytkownik = uzSesja(request)
		studenci = uzytkownik.student_set.all()
		zmiany = False
	
		dane = request.POST.copy()
		for d in dane:
			print d
			
		print(" ")
		
		if 'imie' in dane:
			print('Sprawdzam imie...')
			if sprImie(dane['imie']):
				uzytkownik.imie = dane['imie']
				zmiany = True
				print('Imie ok')
			else:
				print('Blad w imieniu')
				return HttpResponse('Fail')
		
		if 'nazwisko' in dane:
			print('Sprawdzam nazwisko...')
			if sprNazwisko(dane['nazwisko']):
				uzytkownik.nazwisko = dane['nazwisko']
				zmiany = True
				print('Nazwisko ok')
			else:
				print('Blad w nazwisku')
				return HttpResponse('Fail')
		
		if 'ileWydarzen' in dane:
			print('Sprawdzam wydarzenia...')
			if sprWydarzenia(dane['ileWydarzen']):
				uzytkownik.ileMoichWydarzen = int(dane['ileWydarzen'])
				zmiany = True
				print('Wydarzenia ok')
			else:
				print('Blad w ilosci wydarzen')
				return HttpResponse('Fail')
		
		for s in studenci:
			semestr = 'semestr'+str(s.id)
			kierunek = 'kierunek'+str(s.id)
			stopien = 'stopien'+str(s.id)
			print('Sprawdzam kierunki studenta')
			if semestr in dane and kierunek in dane and stopien in dane:
				print('Nastapila proba zmiany kierunku dla studenta nr ' + str(s.id))
				if sprSemestr(dane[kierunek], dane[stopien], dane[semestr]):
					s.semestr = int(dane[semestr])
					s.kierunek_id = int(dane[kierunek])
					s.rodzajStudiow = int(dane[stopien])
					zmiany = True
					print('Kierunek, semestr i stopien ok')
				else:
					print('Blad w kierunku, semestrze lub stopniu')
					return HttpResponse('Fail')
					
			
		if zmiany:
			print('Wprowadzono zmiany w koncie')
			uzytkownik.ktoZmienilDane.id = uzytkownik.id
			uzytkownik.dataOstZmianyDanych = datetime.date.today()
			for s in studenci:
				s.save()
			uzytkownik.save()
			print('Zmiany zostały zapisane. KONIEC')
			return HttpResponse('Ok')
		else:
			return HttpResponse('0')

# Zmiana hasla - wywolana ajaxem - zwraca numer określający odpowiedź (0-5)
def zmienHaslo(request):
	if post(request):
		dane = request.POST.copy()
		student = studSesja(request)
		uzytkownik = student.uzytkownik
		if 'haslo' in dane and 'haslo2' in dane and 'stareHaslo' in dane:
			print('Sprawdzam hasla...')
			#stare haslo sie zgadza
			if(sha256_crypt.verify(dane['stareHaslo'], uzytkownik.haslo)):
				#nowe hasla są takie same
				if(dane['haslo'] == dane['haslo2']):
					#nowe haslo jest rozne od starego
					if(dane['haslo'] != dane['stareHaslo']):
						#nowe haslo spelnia wymagnia
						if(pasuje('^(?!.*(.)\1{3})((?=.*[\d])(?=.*[A-Za-z])|(?=.*[^\w\d\s])(?=.*[A-Za-z])).{8,20}$', dane['haslo'])):
							uzytkownik.haslo = sha256_crypt.encrypt(dane['haslo'])
							uzytkownik.dataOstZmianyHasla = datetime.date.today()
							uzytkownik.save()
							return HttpResponse('0')
						else:
							return HttpResponse('1')
					else:
						return HttpResponse('2')
				else:
					return HttpResponse('3')
			else:
				return HttpResponse('4')
	return HttpResponse('5')
			

def dodajKierunek(request):
	try:
		uzytkownik = uzSesja(request)
		print("1")
		studenci = models.Student.objects.filter(uzytkownik = uzytkownik, uprawnienia__gte = 0)
		print("2")
		dane = request.POST.copy()
		print("3")
		kierunek = dane['kierunek']
		stopien = dane['stopien']
		semestr = dane['semestr']
		print("4")
		print('zaraz sprawdze')
		if sprSemestr(kierunek, stopien, semestr):
			for s in studenci:
				if int(kierunek) == s.kierunek.id and int(stopien) == s.rodzajStudiow:
					return HttpResponse('1') # student jest już na wybranym kierunku
			kierr = models.Kierunek.objects.get(id = int(kierunek))
			student = models.Student(uzytkownik = uzytkownik, indeks = studenci[0].indeks, kierunek = kierr, semestr = int(semestr), rodzajStudiow = int(stopien))
			student.save()
			return HttpResponse('0') # ok
		print('nie przeszlo')
		return HttpResponse('2') # fail
	except:
		print('wystapil wyjatek')
		return HttpResponse('2') # fail



#Wysyłanie maila do admina, gdy nie mozna zmienic pewnych danych w koncie - wywolane ajaxem - zwraca 'Ok' lub 'Fail'
def wyslijEmailZProsba(request):
	try:
		do = "pwrtracker@gmail.com"
		od = "pwrtracker@gmail.com"
		mailZwrotny = uzSesja(request).mail.encode('utf-8')
		tresc = request.POST['textarea_request'].encode('utf-8')

		send_mail('Prośba o edycję konta', tresc+ "\n\nWiadomość wysłana od\n" + mailZwrotny, od, [do], fail_silently=False)
		send_mail("PwrTracker - prośba o edycję danych.",
				  "Wysłałeś wiadomość o następującej treści:\n\n" + tresc,
				  od,
				  [mailZwrotny],
				  fail_silently=False)

		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')