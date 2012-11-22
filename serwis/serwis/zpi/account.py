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
	ileKierunkow = studenci.count()
	wydzialy = models.Wydzial.objects.all()
	wydzialyId = wydzialy.values_list('id', flat = True)
	kierunki = models.Kierunek.objects.all().order_by('nazwa')
	return render_to_response('account.html', {'studenci':studenci, 'uzytkownik':uzytkownik, 'wydzialy':wydzialy, 'ileKierunkow':ileKierunkow, 'kierunki':kierunki})


def edytujDane(request):
	if post(request):
		print("----------------------------------------------")
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
				print('blad w imieniu')
				return HttpResponse('Fail')
		
		if 'nazwisko' in dane:
			print('Sprawdzam nazwisko...')
			if sprNazwisko(dane['nazwisko']):
				uzytkownik.nazwisko = dane['nazwisko']
				zmiany = True
				print('Nazwisko ok')
			else:
				print('blad w nazwisku')
				return HttpResponse('Fail')
		
		if 'ileWydarzen' in dane:
			print('Sprawdzam wydarzenia...')
			if sprWydarzenia(dane['ileWydarzen']):
				uzytkownik.ileMoichWydarzen = int(dane['ileWydarzen'])
				zmiany = True
				print('Wydarzenia ok')
			else:
				print('blad w ilosci wydarzen')
				bledy.append('ileWydarzen ')
		
		for s in studenci:
			semestr = 'semestr'+str(s.id)
			kierunek = 'kierunek'+str(s.id)
			stopien = 'stopien'+str(s.id)
			print('zaraz sprawdz kierunki itpdd')
			if semestr in dane and kierunek in dane and stopien in dane:
				print('da te dane')
				if sprSemestr(dane[kierunek], dane[stopien], dane[semestr]):
					s.semestr = int(dane[semestr])
					s.kierunek_id = int(dane[kierunek])
					s.rodzajStudiow = int(dane[stopien])
					zmiany = True
					print('oki')
				else:
					print('blad w kierunku itp')
					return HttpResponse('Fail')
					
			
		if zmiany:
			uzytkownik.ktoZmienilDane.id = uzytkownik.id
			uzytkownik.dataOstZmianyDanych = datetime.date.today()
			print('mhmm')
			for s in studenci:
				s.save()
			uzytkownik.save()
			print('udalo sie')
			return HttpResponse('Ok')
		else:
			return HttpResponse('0')


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

		send_mail('Prośba o edycję konta', tresc+ "\n\nWiadomość wysłana od\n" + mailZwrotny, od, [do], fail_silently=False)
		send_mail("PwrTracker - prośba o edycję danych.",
				  "Wysłałeś wiadomość o następującej treści:\n\n" + tresc,
				  od,
				  [mailZwrotny],
				  fail_silently=False)

		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')
	
	