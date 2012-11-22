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
	response.write(' <a href=# id= "' + idw + '" onclick="showPlan(this)">Zobacz plan! </a>')
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
