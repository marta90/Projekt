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

def pobierzZajecia(request, start, end):
    if jestSesja(request):
        st = studSesja(request)
        uz = st.uzytkownik
        wynik = ""          #Zmienna tymczasowa
        output = {          # Wynik jaki zostanie wyslany jsonem
            "events": []
        }
        start = start.split("-")        # rozdzielam przeslana mi date startu
        end = end.split("-")            # rozdzielam przeslana mi date konca
        startDate = datetime.date(int(start[0]),int(start[1])+1,int(start[2]))  # tworze date jako obiekt datetime.date
        endDate = datetime.date(int(end[0]),int(end[1])+1,int(end[2]))
        czyParzysty = czyParzystyTydzien(startDate)                             # sprawdzam czy tydzien jest tygodniem parzystym
        planPn = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'pn').order_by('grupa__godzinaOd')   # pobieram z bazy zajecia
        planWt = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'wt').order_by('grupa__godzinaOd')
        planSr = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'śr').order_by('grupa__godzinaOd')
        planCzw = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'cz').order_by('grupa__godzinaOd')
        planPi = models.Plan.objects.filter(uzytkownik = uz.id, grupa__dzienTygodnia = 'pt').order_by('grupa__godzinaOd')
        for i in range(0, 5):       # petla od 0 do 4 
            nowaData = startDate + datetime.timedelta(days=i)   # dodaje do daty poczatkowej okreslona ilosc dni, aby odnalezc wszystkie dni tygodnia
            if nowaData.strftime("%w") == '1':        #poniedzialek
                utworzZajecia(planPn, output, nowaData, czyParzysty, wynik)     # utworzenie zajec z poniedzialku
            if nowaData.strftime("%w") == '2':        #wtorek
                utworzZajecia(planWt, output, nowaData, czyParzysty, wynik)
            if nowaData.strftime("%w") == '3':        #sroda
                utworzZajecia(planSr, output, nowaData, czyParzysty, wynik)
            if nowaData.strftime("%w") == '4':        #czwartek
                utworzZajecia(planCzw, output, nowaData, czyParzysty, wynik)
            if nowaData.strftime("%w") == '5':        #piatek
                utworzZajecia(planPi, output, nowaData, czyParzysty, wynik)
        
        #return HttpResponse(wynik)
        return HttpResponse(simplejson.dumps(output), mimetype="application/json")
        
def utworzZajecia(plan, output, nowaData, czyParzysty, wynik):
    for i in range(0, len(plan)):       # przechodze po liscie zajec
        if (plan[i].grupa.godzinaOd != None):         # sprawdzam czy maja godzine i 
            if (plan[i].grupa.parzystosc == ''):      # czy nie maja okreslonej parzystosci
                tworzenieZajec(i, nowaData, plan, output)                                   # tworze dla znalezionych zajec json
            else:
                if((plan[i].grupa.parzystosc == 'TN') & (czyParzysty == False)):            # sprawdzam czy tydzien jest nie parzysty i dodaje te zajecia
                    tworzenieZajec(i, nowaData, plan, output)
                if((plan[i].grupa.parzystosc == 'TP') & (czyParzysty == True)):             # sprawdzam czy tydzien jest parzysty i dodaje te zajecia
                    tworzenieZajec(i, nowaData, plan, output)

def tworzenieZajec(i, nowaData, plan, output):      # tworze json i dodaje go do listy events
    event = {"id": str(i),
                    "start": "" + str(nowaData.year) + ":" + str(nowaData.month -1) + ":" + str(nowaData.day) + ":" + str(plan[i].grupa.godzinaOd.hour) + ":" + str(plan[i].grupa.godzinaOd.minute),
                    "end": "" + str(nowaData.year) + ":" + str(nowaData.month -1) + ":" + str(nowaData.day) + ":" + str(plan[i].grupa.godzinaDo.hour) + ":" + str(plan[i].grupa.godzinaDo.minute),
                    "title": "(" + plan[i].grupa.kurs.rodzaj + ") " +  plan[i].grupa.kurs.nazwa + "<br>" + plan[i].grupa.prowadzacy.tytul + " " +
                                plan[i].grupa.prowadzacy.imie + " " + plan[i].grupa.prowadzacy.nazwisko + "<br>" + plan[i].grupa.miejsce  + ", " + plan[i].grupa.godzinaOd.strftime('%H:%M') + "-" + plan[i].grupa.godzinaDo.strftime('%H:%M')
                                            }
    output.get("events").append(event)
