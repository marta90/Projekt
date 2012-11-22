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


def saWPoscie(request, dane):
	for d in dane:
		if d not in request.POST.keys():
			return False
		else:
			return True
                    
def czyParzystyTydzien(data):           # sprawdzam czy tydzien jest parzysty
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