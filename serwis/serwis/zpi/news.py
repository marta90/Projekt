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
	studenci = models.Student.objects.filter(uzytkownik = uzytkownik, uprawnienia__gte = 0)
	ileKierunkow = studenci.count()
	dataMin = datetime.date.today()
	ileWydarzen = uzytkownik.ileMoichWydarzen
	dataMax = dataMin + datetime.timedelta(days = ileWydarzen+1)
	mojeWydarzenia = uzytkownik.wydarzenie_set.filter(dataWydarzenia__gte = dataMin, dataWydarzenia__lte = dataMax).order_by('dataWydarzenia', 'godzinaOd')
	wydarzenia = filtrujNoweWydarzenia(student) #zwraca wydarzenia odpowiednie tylko dla wybranego uzytkownika
	wydarzeniaUz = uzytkownik.wydarzenie_set.all() #zbior wydarzen znajdujacych sie w kalendarzu uzytkownika
	wydarzenia = wydarzenia.exclude(id__in=wydarzeniaUz) #pokazanie tylko tych wydarzen, ktorych nie ma w kalendarzu uzytkownika
	wydarzenia = wydarzenia.filter(dataWydarzenia__gte = datetime.date.today())
	wydarzenia = wydarzenia.order_by('-dataDodaniaWyd', '-godzinaOd')[:10]
	dzisiaj = datetime.datetime.now()
	wczoraj = dzisiaj - datetime.timedelta(days = 1)
	return render_to_response('news.html', {'rozmowy':shoutbox, 'mojeWydarzenia':mojeWydarzenia, 'wydarzenia':wydarzenia, 'dzisiaj':dzisiaj, 'wczoraj':wczoraj, 'studenci':studenci, 'ileKierunkow':ileKierunkow})


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


def oznaczWaznyShout(request):
	try:
		idSh = request.POST['shoutId']
		student = studSesja(request)
		uzytkownik = student.uzytkownik
		shout = models.Shoutbox.objects.get(id = idSh)
		shout.czyWazne = true
		shout.save()
		return HttpResponse('Ok')
	except:
		return HttpResponse('Fail')
	
def oznaczNiewaznyShout(request):
	try:
		idSh = request.POST['shoutId']
		student = studSesja(request)
		uzytkownik = student.uzytkownik
		shout = models.Shoutbox.objects.get(id = idSh)
	except:
		return HttpResponse('Fail')
	if shout.student == student:
		shout.czyWazne = false
		shout.save()
		return HttpResponse('Ok')
	else:
		return HttpResponse('Forbidden')
	



# Dodanie wydarzenia z listy do własnego kalendarza
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
		

# Zmiana shoutboxa na inny kierunek (zmiana id w sesji)
def zamienStudenta(request, idS):
	request.session['studentId'] = idS
	return zaladujShoutbox(request)
