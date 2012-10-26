from django.shortcuts import render_to_response
from serwis.zpi import models
from django.http import HttpResponse, HttpResponseRedirect
from passlib.hash import sha256_crypt
from django.core.mail import send_mail
from BeautifulSoup import BeautifulSoup, NavigableString, Tag   #parser kodu html
from django.db import transaction
import time, datetime
import os
import string
import random
import re

# Wyswietlenie strony glownej
def glowna(request):
	if jestSesja(request):
		nick = request.session['nick']
		return render_to_response('index.html', {'nick':nick, 'wyloguj':"wyloguj"}) #DODAC WYSWIETLANIE ZALOGOWANEGO UZYTKOWNIKA
	else:
		return render_to_response('index.html', {'logowanie':True}) #TU MA BYC NA STRONIE MENU Z LOGOWANIEM

# Sprawdzenie czy sesja jest otwarta
def jestSesja(request):
	return ('nick' in request.session) & ('idUz' in request.session)

# Wyswietlenie rejestracji
def rejestruj(request):
    if request.method == 'POST':
        nick = request.POST['fld_loginCheck']
        indeks = request.POST['fld_indexNumber']
        wydz = models.Wydzial.objects.all()
        return render_to_response('registration.html', {'nick': nick, 'index': indeks, 'wydzialy': wydz})
    else:
        return HttpResponse("Nie sprawdzono poprawności loginu oraz numer indeksu.")

# Rejestracja użytkownika - trzeba się jeszcze pobawić ze sprawdzaniem danych (regex)
@transaction.commit_on_success
def zarejestruj(request):
    if request.method == 'POST':
        nick = request.POST['fld_nick']
        indeks = request.POST['fld_index']
        haslo = sha256_crypt.encrypt(request.POST['fld_pass'])
        imie = request.POST['fld_name']
        nazwisko = request.POST['fld_lastName']
        semestr = request.POST['fld_semester']
        kierunek = models.Kierunek.objects.get(id = request.POST['select_faculty'])
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
        return render_to_response('index.html', {'alert': "Na Twojego maila studenckiego został wysłany link z aktywacją konta."})

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
	tresc = tresc + "http://127.0.0.1:8000/confirm/" + student.aktywator + "/" + student.indeks.encode('utf-8')
	send_mail(tytul, tresc, 'pwrtracker@gmail.com', [student.indeks + "@student.pwr.wroc.pl"], fail_silently=False)
	
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
	
def jestStudentem(uzytkownik):
	st = models.Student.objects.filter(uzytkownik=uzytkownik)
	odp = st.exists()
	return odp

def czyZmienicHaslo(uzytkownik):
    dzisiaj = datetime.date.today()
    dataZmianyHasla = uzytkownik.dataOstZmianyHasla.date()
    dni = (dzisiaj - dataZmianyHasla)
    if(dni.days) > 29:
        return True
    else:
        return False

# Logowanie	
def logowanie(request):  #Dodaj sprawdzanie aktywacje i sprawdzanie hasla > 30 dni
    if request.method == 'POST':
        zlyLogin = 'Podany login i/lub hasło są nieprawidłowe.'
        bladWyslania = 'Wystąpił błąd. Spróbuj ponownie.'
        zmienHaslo = 'Coś ze zmianą hasła'
        nickPost = request.POST['fld_login']
        hasloPost = request.POST['fld_pass']
        uz = models.Uzytkownik.objects.filter(nick=nickPost)
        if uz.exists():
            uzytkownik = models.Uzytkownik.objects.get(nick=nickPost)
            haslo = uzytkownik.haslo
            zgodnosc = sha256_crypt.verify(hasloPost, haslo)
            if(zgodnosc):
                if jestStudentem(uzytkownik):
                    student = models.Student.objects.get(uzytkownik=uzytkownik)
                    if student.czyAktywowano:
                        if czyZmienicHaslo(uzytkownik):
                            return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu': zmienHaslo, 'zmianaHasla': True})
                        else:
                            request.session['nick'] = nickPost # SESJA
                            request.session['idUz'] = models.Uzytkownik.objects.get(nick=nickPost).id # SESJA
                            return HttpResponseRedirect('/')
                    else:
                        return HttpResponse('Musisz aktywować konto, aby móc się zalogować. Jeśli chcesz wysłać aktywator jeszcze raz kliknij w poniższy link')
                else:
                    if czyZmienicHaslo(uzytkownik):
                        return HttpResponse('Trzeba zmienić hasło')
                    else:
                        request.session['nick'] = nickPost # SESJA
                        request.session['idUz'] = models.Uzytkownik.objects.get(nick=nickPost).id # SESJA
                        return HttpResponseRedirect('/')
            else:
                    return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':zlyLogin})
        else:
                return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':zlyLogin})
                #return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu': zmienHaslo, 'zmianaHasla': True})
    else:
            return render_to_response('index.html', {'logowanie':True, 'blad':True, 'tekstBledu':bladWyslania})

def wylogowanie(request):
	try:
		for elemSesji in request.session.keys():
			del request.session[elemSesji]
	except KeyError:
		pass
	return HttpResponseRedirect('/')

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

#Pobranie kierunków dla okreslonych wydzialow. Potrzebne przy rejestracji
def pobierzKierunki(request, idWydz):
    kierunki = models.Kierunek.objects.filter(wydzial__id=idWydz)
    odp = '<option value=0>Wybierz kierunek...</option>'
    for k in kierunki:
        #odp = odp + 'obj.options[obj.options.length] = new Option(\''+ k.nazwa +'\' , \'' + str(k.id) + '\'); '
        odp = odp + '<option value=\'' + str(k.id) +'\'>' + k.nazwa + '</option>'
    return HttpResponse(odp)

#Pobieranie Semestrów dla poszczególnych kierunków i typu studiów. Potrzebne przy rejestracji
def pobierzSemestry(request, idSpec, idTyp):
    k = models.Kierunek.objects.get(id=idSpec)
    odp = ""
    if idTyp == "1":
        for i in range(1, k.liczbaSemestrow1st + 1):
            odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
    if idTyp == "2":
        for i in range(1, k.liczbaSemestrow2stPoInz + 1):
            odp = odp + '<option value=\'' + str(i) +'\'>' + str(i) + '</option>'
    return HttpResponse(odp)

# Zaladowanie strony portal.html do diva na stronie glownej
def zaladujPortal(request):
	return render_to_response('portal.html')

# Zaladowanie strony timetable.html do diva na stronie glownej
def zaladujPlan(request):
	if jestSesja(request):
		return render_to_response('timetable.html')
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")

# Zaladowanie strony calendar.html do diva na stronie glownej
def zaladujKalendarz(request):
	if jestSesja(request):
		return render_to_response('calendar.html')
	else:
		return HttpResponse("\nDostęp do wybranej treści możliwy jest jedynie po zalogowaniu do serwisu.")

# Zaladowanie strony teachers.html do diva na stronie glownej
def zaladujWykladowcow(request):
	return render_to_response('teachers.html')

# Zaladowanie strony map.html do diva na stronie glownej
def zaladujMape(request):
	return render_to_response('map.html')

# Zaladowanie strony account.html do diva na stronie glownej
def zaladujKonto(request):
	return render_to_response('account.html')

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

def generujPlan(request):
    if request.method == 'POST':
        html = request.POST['htmlPWR']
        parser = BeautifulSoup(''.join(html))
        text = ''       #Wypisuje jesli nic nie ma
        for i in parser.findAll('tr'):
            # tabelaA - tabela zapisow normalnych, tabelaB - tabela zapisow administracyjnych
            tabelaA = i.findChildren('a', {'name': re.compile('^hrefZapisaneGrupySluchaczaTabela\d{7}$')}, False) #False wskazuje ze rekursja jest wylaczona
            tabelaB = i.findChildren('a', {'name': re.compile('^hrefZapisaneAdminGrupySluchaczaTabela\d{7}$')}, False) #False wskazuje ze rekursja jest wylaczona
            if len(tabelaA) > 0:    # Jesli sa jakies zapisy
                k = models.Kurs()          # obiekt bazy tabeli Kurs
                g = models.Grupa()         # obiekt bazy tabeli Grupa
                p = models.Prowadzacy()    # obiekt bazy tabeli Prowadzacy
                pl = models.Plan()         # obiekt bazy tabeli Plan - GrupyStudentow
                uz = models.Uzytkownik.objects.get(nick = request.session['nick'])
                
                # KURS
                kodGrupy = tabelaA[0].findNextSibling('td')
                kodGrupyTxt = kodGrupy.string.strip()    # pobranie kodu grupy
                kodKursu = kodGrupy.findNextSibling('td')
                kodKursuTxt = kodKursu.string.strip()    # pobranie kodu kursu
                nazwa = kodKursu.findNextSibling('td')
                nazwaKursuTxt = nazwa.string.strip()     # pobranie nazwy kursu
                kodBlokuKursow = i.findNextSibling('tr')
                prowadzacyIPkt = kodBlokuKursow.findNextSibling('tr')
                dzieciprowadzacyIPkt = prowadzacyIPkt.findChildren('td', False)     # znalezienie wszystkich dzieci "td" od wiersza tr
                rodzajKursu = dzieciprowadzacyIPkt[1]
                rodzajKursuTxt = rodzajKursu.string.strip().encode('utf-8')      # pobranie rodzaju kursu
                rodzajKursuTxtKrotki = {    # Switch
                    'Wykład': 'W',          # Jesli jest Wyklad to do rdzKursuTxtKrotki przypisane jest W
                    'Zajęcia laboratoryjne': 'L',
                    'Praktyka': 'P',
                    'Seminarium': 'S',
                    'Projekt': 'P'
                }[rodzajKursuTxt]           # Co sprawdzamy w Case
                punktyECTS = dzieciprowadzacyIPkt[len(dzieciprowadzacyIPkt)-1].string.strip()
                #zapis do bazy Kursu
                czyJestKurs = models.Kurs.objects.filter(nazwa = nazwaKursuTxt, rodzaj = rodzajKursuTxtKrotki, ects = punktyECTS, kodKursu = kodKursuTxt)
                if (not (czyJestKurs.exists())):
                    k.nazwa = nazwaKursuTxt
                    k.rodzaj = rodzajKursuTxtKrotki
                    k.ects = punktyECTS
                    k.kodKursu = kodKursuTxt
                    k.save()
                
                # PROWADZACY
                prow  = dzieciprowadzacyIPkt[0]
                imieNazwProw = prow.string.strip().split() # oddzielenie imienia od nazwiska
                tytulProw = ''                              # Tytul prowadzacego
                dlLisProw = len(imieNazwProw)       # rozmiar listy z tytulemProw imieniem i nazwiskiem
                for i in range(0, dlLisProw-3):     # Odczytanie tytulu
                    tytulProw += imieNazwProw[i] + " "
                tytulProw += imieNazwProw[dlLisProw-3]
                imieProw = imieNazwProw[dlLisProw-1]        #Odczytanie imienia
                nazwiskoProw = imieNazwProw[dlLisProw-2]    #Odczytanie nazwiska
                coProw = prow.findNextSibling('td')
                #zapis do bazy Prowadzacego
                czyJestProw = models.Prowadzacy.objects.filter(imie = imieProw, nazwisko = nazwiskoProw, tytul = tytulProw)
                if (not (czyJestProw.exists())):
                    p.imie = imieProw
                    p.nazwisko = nazwiskoProw
                    p.tytul = tytulProw
                    p.ktoWprowadzil = uz
                    p.dataOstZmianyDanych =  datetime.date.today()
                    p.ktoZmienilDane = uz
                    p.save()
                    
                # GODZINY I MIEJSCE
                prowadzacyGrupy = models.Prowadzacy.objects.get(imie = imieProw, nazwisko = nazwiskoProw, tytul = tytulProw)
                kursGrupy = models.Kurs.objects.get(nazwa = nazwaKursuTxt, rodzaj = rodzajKursuTxtKrotki, ects = punktyECTS, kodKursu = kodKursuTxt)
                godziny = prowadzacyIPkt.findNextSibling('tr')
                dataMiejsce = godziny.next.findNextSibling('td').findChildren('td')
                
                miejsce = ""
                dzien = ""
                parz = ""
                godzR = None
                godzZ = None
                
                for dm in dataMiejsce:
                    listaDM = dm.string.split(',', 1)   # oddzielenie daty od miejsca
                    if listaDM[0].strip() != "bez terminu":
                        miejsce = listaDM[1][1:]            # pobranie miejsca
                        listaDG = listaDM[0].split()    # odzielenie dnia od godziny
                        dzienIParz = listaDG[0].split('/', 1)   # oddzielenie dnia od parzystosci
                        if (len(dzienIParz) == 1):
                            dzien = dzienIParz[0]
                        else:
                            dzien = dzienIParz[0]
                            parz = dzienIParz[1]
                        godz = listaDG[1].split('-', 1) # oddzielenie godz rozp od zak
                        godzR = godz[0]           
                        godzZ = godz[1]
                        #zapis do bazy Grupy
                        czyJestGrupa = models.Grupa.objects.filter(kodGrupy = kodGrupyTxt, prowadzacy = prowadzacyGrupy, dzienTygodnia = dzien, parzystosc = parz,
                                                                   godzinaOd = godzR, godzinaDo = godzZ, miejsce=miejsce, kurs = kursGrupy)
                        if( not(czyJestGrupa.exists())):
                            g.kodGrupy = kodGrupyTxt
                            g.prowadzacy = prowadzacyGrupy
                            g.dzienTygodnia = dzien
                            g.parzystosc = parz
                            g.godzinaOd = godzR
                            g.godzinaDo = godzZ
                            g.miejsce = miejsce
                            g.kurs = kursGrupy
                            g.save()
                    else:
                        czyJestGrupa = models.Grupa.objects.filter(kodGrupy = kodGrupyTxt, prowadzacy = prowadzacyGrupy, dzienTygodnia = dzien, parzystosc = parz,
                                                                   godzinaOd = godzR, godzinaDo = godzZ, miejsce=miejsce, kurs = kursGrupy)
                        if( not(czyJestGrupa.exists())):
                            g.kodGrupy = kodGrupyTxt
                            g.prowadzacy = prowadzacyGrupy
                            g.dzienTygodnia = dzien
                            g.parzystosc = parz
                            g.miejsce = miejsce
                            g.kurs = kursGrupy
                            g.save()
                            
                # ZAPISANIE TYCH GRUP DO STUDENTA
                student = models.Student.objects.get(uzytkownik = uz)
                grupa = models.Grupa.objects.get(kodGrupy = kodGrupyTxt, prowadzacy = prowadzacyGrupy, dzienTygodnia = dzien, parzystosc = parz,
                                                godzinaOd = godzR, godzinaDo = godzZ, miejsce=miejsce, kurs = kursGrupy)
                if not(models.Plan.objects.filter(student = student, grupa = grupa).exists()):
                    pl.student = student
                    pl.grupa = grupa
                    pl.save()
                    
            #if len(tabelaB) < 0:        # Jesli sa zapisy administracyjne
            #    czyKursZaoczny = False;
            #    z = Zajecia()           # obiekt bazy tabeli Zajecia
            #    kodGrupy = tabelaA[0].findNextSibling('td')
            #    z.kodGrupy = kodGrupy.string.strip()    # pobranie kodu grupy
            #    kodKursu = kodGrupy.findNextSibling('td')
            #    z.kodKursu = kodKursu.string.strip()    # pobranie kodu kursu
            #    nazwa = kodKursu.findNextSibling('td')
            #    z.nazwa = nazwa.string.strip()          # pobranie nazwy kursu
            #    kodBlokuKursow = i.findNextSibling('tr')
            #    prowadzacyIPkt = kodBlokuKursow.findNextSibling('tr')
            #    prow = prowadzacyIPkt.next.findNextSibling('td')
            #    z.prowadzacy = prow.string.strip()      # pobranie prowadzacego
            #    coProw = prow.findNextSibling('td')
            #    z.coProwadzi = coProw.string.strip()    # pobranie tego co prowadzi
            #    godziny = prowadzacyIPkt.findNextSibling('tr')
            #    dataMiejsce = godziny.next.findNextSibling('td').findChildren('td')
            #    for dm in dataMiejsce:
            #        dgm = DGM()                         # obiekt bazy tabeli DGM
            #        dz = DZ()                           # obiekt bazy tabeli DZ
            #        listaDM = dm.string.split(',', 1)
            #        if listaDM[0].strip() != "bez terminu":
            #            miejsce = listaDM[1]
            #            listaDG = listaDM[0].split()
            #            dzien = listaDG[0]
            #            logiczny = re.search('^(\d{2,4})-(\d{2})-(\d{2})$', dzien)
            #            if logiczny == None:
            #                godz = listaDG[1].split('-', 1)
            #                godzR = godz[0]
            #                godzZ = godz[1]
            #                z.setNowaDGM(dzien, godzR, godzZ, miejsce)
            #            else:
            #                czyKursZaoczny = True;
            #    if czyKursZaoczny == False:
            #        listaZajec.append(z) 
    else:
        text = 'Nic nie ma'
    return HttpResponse("____+++GIIIIIIIT!")
