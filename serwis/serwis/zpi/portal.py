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

from serwis.zpi.news import zaladujNewsy


############### PORTAL ####################################################################

# Zaladowanie strony portal.html do diva na stronie glownej
def zaladujPortal(request):
	if jestSesja(request):
		return zaladujNewsy(request)
	elif 'komRej' in request.session:
		kom = request.session['komRej']
		# Poprawny przebieg rejestracji
		if kom == 'rejestracja_ok':
			tekst = "PWRTracker - na Twojego maila studenckiego został wysłany link z aktywacją konta. Kliknij go, aby potwierdzić rejestrację w serwisie."

		# Dane nie spelniaja ograniczen
		elif kom == 'ograniczenia':
			tekst = "Dane nie spełniają wymaganych ograniczeń. Spróbuj ponownie."
		
		# Nie przesłano wszystkich danych
		elif kom == 'niepelne_dane':
			tekst = "Wystąpił błąd podczas rejestracji. Spróbuj ponownie."
		
		# Blad wysylania	
		elif kom == 'blad_ogolny':
			tekst = "Wystąpił błąd podczas rejestracji. Spróbuj ponownie."
		
		elif kom == 'aktywacja_ok':
			tekst = "Aktywacja przebiegła pomyślnie. Możesz się zalogować."
		
		elif kom == 'aktywacja_anuluj':
			tekst = "Aktywację anulowane. Konto zostało usunięte."
			
		usunSesje(request)
		return render_to_response('portal.html', {'alert':tekst})	
	else:
		return render_to_response('portal.html')


