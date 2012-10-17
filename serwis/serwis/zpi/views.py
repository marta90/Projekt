﻿from django.shortcuts import render_to_response
from serwis.zpi import models
from django.http import HttpResponse, HttpResponseRedirect
from passlib.hash import sha256_crypt
from django.core.mail import send_mail
from django.db import transaction
import time, datetime
import os
import string
import random
import re

# Wyswietlenie strony glownej
def glowna(request):
	if ('nick' in request.session) & ('idUz' in request.session):
		return render_to_response('index.html') #DODAC WYSWIETLANIE ZALOGOWANEGO UZYTKOWNIKA
	else:
		return render_to_response('index.html') #TU MA BYC NA STRONIE MENU Z LOGOWANIEM

# Wyswietlenie rejestracji
def rejestruj(request):
	if request.method == 'POST':
		nick = request.POST['fld_loginCheck']
		indeks = request.POST['fld_indexNumber']
		return render_to_response('kod.html', {'nick': nick, 'index': indeks})
	else:
		return HttpResponse("Nie sprawdzono poprawności loginu oraz numer indeksu.")

# Rejestracja użytkownika - trzeba się jeszcze pobawić ze sprawdzaniem danych (regex)
@transaction.commit_on_success
def zarejestruj(request):
	nick = request.POST['fld_nick']
	indeks = request.POST['fld_index']
	haslo = request.POST['fld_pass']
	imie = request.POST['fld_name']
	nazwisko = request.POST['fld_lastName']
	semestr = request.POST['fld_semester']
	kierunek = models.Kierunek.objects.get(id = request.POST['fld_specialization'])
	stopienStudiow = request.POST['select_type']
	uzytkownik = models.Uzytkownik(nick = nick, imie = imie, nazwisko = nazwisko, haslo = haslo, mail = indeks + "@student.pwr.wroc.pl")
	uzytkownik.save()
	uzytkownik.ktoWprowadzil = models.Uzytkownik.objects.get(id = uzytkownik.id)
	uzytkownik.ktoZmienilDane = models.Uzytkownik.objects.get(id = uzytkownik.id)
	uzytkownik.dataOstLogowania = datetime.date.today()
	uzytkownik.dataOstZmianyHasla = datetime.date.today()
	uzytkownik.dataOstZmianyDanych = datetime.date.today()
	uzytkownik.save()
	student = models.Student(uzytkownik = models.Uzytkownik.objects.get(id = uzytkownik.id), indeks = indeks)
	student.save()
	student.aktywator = wygenerujAktywator()
	student.save()
	kierunki = models.KierunkiStudenta(student = student, kierunek = kierunek, rodzajStudiow = stopienStudiow, semestr = semestr)
	kierunki.save()
	wyslijPotwierdzenie(student)
	return HttpResponse("Wyslano aktywator")

# Generacja kodu do aktywacji konta
def wygenerujAktywator():
	allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
	import random
	random = random.SystemRandom()
	return ''.join([random.choice(allowed_chars) for i in range(33)])

# Przypomnienie hasla
def przypomnijHaslo(request):
	return 0

# Wyslanie maila z kodem potwierdzajacym rejestracje
def wyslijPotwierdzenie(student):
	tytul = "PwrTracker - potwierdzenie rejestracji"
	tresc = "Witaj na PwrTracker!\n\nAby potwierdzić rejestrację w serwisie kliknij na poniższy link.\n"
	tresc = tresc + "http://127.0.0.1:8000/confirm/" + str(student.aktywator) + "/" + student.indeks
	send_mail(tytul, tresc, '179298@student.pwr.wroc.pl', [student.indeks + "@student.pwr.wroc.pl"], fail_silently=False)
	
# Potwierdzenie rejestracji po kliknieciu w link aktywacyjny
def potwierdzRejestracje(request, aktywator, indeks):
	st = models.Student.objects.filter(indeks=indeks)
	if st.exists():
		student = models.Student.objects.get(indeks=indeks)
		if student.aktywator == aktywator:
			student.czyAktywowano = True
			student.save()
			return HttpResponse("Udało się aktywować")
	return HttpResponse("Aktywacja zakończona niepowodzeniem. Spróbuj jeszcze raz")		
			
# Logowanie	
def logowanie(request):
	if request.method == 'POST':
		nickPost = request.POST['fld_login']
		hasloPost = request.POST['fld_pass']
		uz = models.Uzytkownik.objects.filter(nick=nickPost)
		if uz.exists():
			haslo = models.Uzytkownik.objects.get(nick=nickPost).haslo
			zgodnosc = sha256_crypt.verify(hasloPost, haslo)
			if(zgodnosc):
				request.session['nick'] = nickPost # SESJA
				request.session['idUz'] = models.Uzytkownik.objects.get(nick=nickPost).id # SESJA
				return HttpResponse(zgodnosc)
			else:
				return HttpResponse('NIE OK')
		else:
			return HttpResponse('NIE OK')

# Sprawdzanie nicku - dozwolne znaki oraz unikatowość w bazie danych
def sprawdzNick(request, nick):
	pattern = '^[A-Za-z0-9_-]*$'
	result = re.match(pattern, nick)
	if not result:
		return HttpResponse('denied')
	uzytkownicy = models.Uzytkownik.objects.all()
	for uz in uzytkownicy:
		if nick == uz.nick:
			return HttpResponse('denied')
	return HttpResponse('okay')

# Sprawdzanie indeksu - dozwolne znaki oraz unikatowość w bazie danych
def sprawdzIndeks(request, indeks):
	pattern = '\d{6}'
	result = re.match(pattern, indeks)
	if not result:
		return HttpResponse('denied')
	studenci = models.Student.objects.all()
	for st in studenci:
		if indeks == st.indeks:
			return HttpResponse('denied')
	return HttpResponse('okay')

# Zaladowanie strony portal.html do diva na stronie glownej
def zaladujPortal(request):
	return render_to_response('portal.html')

# Zaladowanie strony timetable.html do diva na stronie glownej
def zaladujPlan(request):
	return render_to_response('timetable.html')

# Zaladowanie strony calendar.html do diva na stronie glownej
def zaladujKalendarz(request):
	return render_to_response('calendar.html')

# Zaladowanie strony teachers.html do diva na stronie glownej
def zaladujWykladowcow(request):
	return render_to_response('teachers.html')

# Zaladowanie strony map.html do diva na stronie glownej
def zaladujMape(request):
	return render_to_response('map.html')

# Wysyłanie maila do admina
def wyslijEmail(request):
	if request.method == 'POST':
		do = "179298@student.pwr.wroc.pl"
		od = "179298@student.pwr.wroc.pl"
		mailZwrotny = request.POST['fld_email'].encode('utf-8')
		tytul = request.POST['fld_topic'].encode('utf-8')
		tresc = request.POST['fld_text'].encode('utf-8')
		send_mail(tytul, tresc+ "\n\nWiadomość wysłana od\n" + mailZwrotny, od, [do], fail_silently=False)
		send_mail("PwrTracker - wysłano wiadomość: " + tytul, "Wysłałeś wiadomość o następującej treści:\n\n" + tresc, od, [mailZwrotny], fail_silently=False)
		return HttpResponse('Wysłano wiadomości')
