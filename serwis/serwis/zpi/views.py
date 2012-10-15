from django.shortcuts import render_to_response
from serwis.zpi import models
from django.http import HttpResponse, HttpResponseRedirect
from passlib.hash import sha256_crypt

# Create your views here.
def glowna(request):
    return render_to_response('index.html')

def logowanie(request):
    if request.method == 'POST':
        nickPost = request.POST['fld_login']
        hasloPost = request.POST['fld_pass']
        models.Uzytkownik.objects
        uz = models.Uzytkownik.objects.filter(nick=nickPost)
        if uz.exists():
            haslo = models.Uzytkownik.objects.get(nick=nickPost).haslo
            true = sha256_crypt.verify(hasloPost, haslo)
            #request.session['nick'] = nickPost # SESJA
            #request.session['idUz'] = models.Uzytkownik.objects.get(nick=nickPost).id # SESJA
            return HttpResponse(true)
        else:
            return HttpResponse('NIE OK')
    #elif 'nick' in request.session:
    #    return HttpResponseRedirect('stronaGlowna.html')
    return render_to_response('logowanie.html')

def sprawdzNick(request, nick):
    uzytkownicy = models.Uzytkownik.objects.all()
    #time.sleep(2)
    for uz in uzytkownicy:
        if nick == uz.nick:
			return HttpResponse('denied')
	return HttpResponse('okay')

def sprawdzIndeks(request, indeks):
    studenci = models.Student.objects.all()
    #time.sleep(2)
    for st in studenci:
	if indeks == st.indeks:
			return HttpResponse('denied')
	return HttpResponse('okay')

def zaladujPortal(request):
	return render_to_response('teachers.html')

def zaladujPlan(request):
	return render_to_response('timetable.html')

def zaladujKalendarz(request):
	return render_to_response('calendar.html')

def zaladujWykladowcow(request):
	return render_to_response('teachers.html')

def zaladujMape(request):
	return render_to_response('map.html')