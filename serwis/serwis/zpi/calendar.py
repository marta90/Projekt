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

############### KALENDARZ #################################################################

# Zaladowanie strony calendar.html do diva na stronie glownej
def zaladujKalendarz(request):
	if jestSesja(request):
		uzytkownik = uzSesja(request)
		grupy = uzytkownik.grupa_set.all()
		return render_to_response('calendar.html', {'grupy':grupy})
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")


def dodajWydarzenie(request):
	if post(request):
		dane = request.POST.copy()
		student = studSesja(request)
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
		print('zaraz utworzy sie wydarzenie')
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
		
def sprNazweWyd(nazwa):
	if len(nazwa) >0 and len(nazwa)<21:
		return True
	else:
		return False
	
def sprOpisWyd(opis):
	if len(opis) >0 and len(opis)<101:
		return True
	else:
		return False
	
def sprGodzine(godzina):
	integer = pasuje('\d+', godzina)
	if integer and int(godzina)>=0 and int(godzina) <24:
		return True
	else:
		return False

def sprMinute(minuta):
	integer = pasuje('\d+', minuta)
	if integer and int(minuta)>=0 and int(minuta) <60:
		return True
	else:
		return False
	
def sprRodzaj(rodzaj):
	if rodzaj == "1" or rodzaj == "2" or rodzaj == "3" or rodzaj == "4" or rodzaj == "5" or rodzaj == "6" or rodzaj == "7":
		return True
	else:
		return False
	
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

def sprDate(dzien, miesiac, rok):
	try:
		data = datetime.date(int(rok), int(miesiac), int(dzien))
		return True
	except:
		return False
		