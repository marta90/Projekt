from BeautifulSoup import BeautifulSoup, NavigableString, Tag   #parser kodu html
from serwis.zpi import models
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
import time, datetime
import re
from django.db import transaction
from django.db.models.signals import post_save

from serwis.zpi import views


# Create your views here.
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
                zapisyNormalne(request, i, tabelaA[0])
            if len(tabelaB) >0:
                zapisyAdministracyjne(request, i, tabelaB[0])
    else:
        text = 'Nic nie ma'
    views.content = 'timetable'
    return HttpResponseRedirect('/')

def zapisyAdministracyjne(request, pierwszyTRZPlanem, pierwszyAZLinkiem):
        czyKursZaoczny = False
        czyKursZapisany = None
        czyProwadzacyZapisany = None
        k = models.Kurs()          # obiekt bazy tabeli Kurs
        g = models.Grupa()         # obiekt bazy tabeli Grupa
        p = models.Prowadzacy()    # obiekt bazy tabeli Prowadzacy
        pl = models.Plan()         # obiekt bazy tabeli Plan - GrupyStudentow
        uz = models.Uzytkownik.objects.get(nick = request.session['nick'])
        
        # KURS
        kodGrupy = pierwszyAZLinkiem.findNextSibling('td')
        kodGrupyTxt = kodGrupy.string.strip()    # pobranie kodu grupy
        kodKursu = kodGrupy.findNextSibling('td')
        kodKursuTxt = kodKursu.string.strip()    # pobranie kodu kursu
        nazwa = kodKursu.findNextSibling('td')
        nazwaKursuTxt = nazwa.string.strip()     # pobranie nazwy kursu
        kodBlokuKursow = pierwszyTRZPlanem.findNextSibling('tr')
        prowadzacyIPkt = kodBlokuKursow.findNextSibling('tr')
        dzieciprowadzacyIPkt = prowadzacyIPkt.findChildren('td', False)     # znalezienie wszystkich dzieci "td" od wiersza tr
        rodzajKursu = dzieciprowadzacyIPkt[1]
        rodzajKursuTxt = rodzajKursu.string.strip().encode('utf-8')      # pobranie rodzaju kursu
        rodzajKursuTxtKrotki = {    # Switch
            'Wykład': 'W',          # Jesli jest Wyklad to do rdzKursuTxtKrotki przypisane jest W
            'Zajęcia laboratoryjne': 'L',
            'Praktyka': 'P',
            'Seminarium': 'S',
            'Projekt': 'P',
            'Ćwiczenia': 'Ć'
        }[rodzajKursuTxt]           # Co sprawdzamy w Case
        if(dzieciprowadzacyIPkt[len(dzieciprowadzacyIPkt)-1].string.strip() != ''): #Czasmi nie ma punktów ECTS
            punktyECTS = dzieciprowadzacyIPkt[len(dzieciprowadzacyIPkt)-1].string.strip()
            if punktyECTS.find(',') != -1:
                punktyECTS = punktyECTS[:punktyECTS.index(',')]         # Czasami te punkty sa zapisane jako np. 3,00 więc pozbywamy się tej reszty :D
        else:
            punktyECTS = '0'    # W przypadku kiedy nie ma podane ECTS
        #zapis do bazy Kursu
        czyJestKurs = models.Kurs.objects.filter(nazwa = nazwaKursuTxt, rodzaj = rodzajKursuTxtKrotki, ects = punktyECTS, kodKursu = kodKursuTxt)
        if (not (czyJestKurs.exists())):
            k.nazwa = nazwaKursuTxt
            k.rodzaj = rodzajKursuTxtKrotki
            k.ects = punktyECTS
            k.kodKursu = kodKursuTxt
            czyKursZapisany = k.save()
        
        # PROWADZACY
        prow  = dzieciprowadzacyIPkt[0]
        imieNazwProw = prow.string.strip().split() # oddzielenie imienia od nazwiska
        tytulProw = ''                              # Tytul prowadzacego
        dlLisProw = len(imieNazwProw)       # rozmiar listy z tytulemProw imieniem i nazwiskiem
        for i in range(0, dlLisProw-3):     # Odczytanie tytulu
            tytulProw += imieNazwProw[i] + " "
        tytulProw += imieNazwProw[dlLisProw-3]
        imieProw = imieNazwProw[dlLisProw-2]        #Odczytanie imienia
        nazwiskoProw = imieNazwProw[dlLisProw-1]    #Odczytanie nazwiska
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
            czyProwadzacyZapisany = p.save()
        
        # GODZINY I MIEJSCE
        prowadzacyGrupy = models.Prowadzacy.objects.get(imie = imieProw, nazwisko = nazwiskoProw, tytul = tytulProw)
        kursGrupy = models.Kurs.objects.get(nazwa = nazwaKursuTxt, rodzaj = rodzajKursuTxtKrotki, ects = punktyECTS, kodKursu = kodKursuTxt)
        godziny = prowadzacyIPkt.findNextSibling('tr')
        dataMiejsce = godziny.next.findNextSibling('td').findChildren('td')
        
        for dm in dataMiejsce:
            g = models.Grupa()         # obiekt bazy tabeli Grupa
            pl = models.Plan()         # obiekt bazy tabeli Plan - GrupyStudentow
            miejsce = ""
            dzien = ""
            parz = ""
            godzR = None
            godzZ = None
            
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
                czyData = re.search('^(\d{2,4})-(\d{2})-(\d{2})$', dzien)   # Od daty zaczyna się dla zaocznych
                if (czyData == None):
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
                        g.save(force_insert=True)
                else:
                    czyKursZaoczny = True
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
        
            if not(czyKursZaoczny):
                # ZAPISANIE TYCH GRUP DO STUDENTA
                student = models.Student.objects.get(uzytkownik = uz)
                g = models.Grupa.objects.get(kodGrupy = kodGrupyTxt, prowadzacy = prowadzacyGrupy, dzienTygodnia = dzien, parzystosc = parz,
                                                           godzinaOd = godzR, godzinaDo = godzZ, miejsce=miejsce, kurs = kursGrupy)
                if not(models.Plan.objects.filter(student = student, grupa = g).exists()):
                    pl.student = student
                    pl.grupa = g
                    pl.save()
            else:
                if (czyKursZapisany):
                    czyKursZapisany.delete()
                if (czyProwadzacyZapisany):
                    czyProwadzacyZapisany.delete()


@transaction.commit_on_success
def zapisyNormalne(request, pierwszyTRZPlanem, pierwszyAZLinkiem):
        k = models.Kurs()          # obiekt bazy tabeli Kurs
        g = models.Grupa()         # obiekt bazy tabeli Grupa
        p = models.Prowadzacy()    # obiekt bazy tabeli Prowadzacy
        pl = models.Plan()         # obiekt bazy tabeli Plan - GrupyStudentow
        uz = models.Uzytkownik.objects.get(nick = request.session['nick'])
        
        # KURS
        kodGrupy = pierwszyAZLinkiem.findNextSibling('td')
        kodGrupyTxt = kodGrupy.string.strip()    # pobranie kodu grupy
        kodKursu = kodGrupy.findNextSibling('td')
        kodKursuTxt = kodKursu.string.strip()    # pobranie kodu kursu
        nazwa = kodKursu.findNextSibling('td')
        nazwaKursuTxt = nazwa.string.strip()     # pobranie nazwy kursu
        kodBlokuKursow = pierwszyTRZPlanem.findNextSibling('tr')
        prowadzacyIPkt = kodBlokuKursow.findNextSibling('tr')
        dzieciprowadzacyIPkt = prowadzacyIPkt.findChildren('td', False)     # znalezienie wszystkich dzieci "td" od wiersza tr
        rodzajKursu = dzieciprowadzacyIPkt[1]
        rodzajKursuTxt = rodzajKursu.string.strip().encode('utf-8')      # pobranie rodzaju kursu
        rodzajKursuTxtKrotki = {    # Switch
            'Wykład': 'W',          # Jesli jest Wyklad to do rdzKursuTxtKrotki przypisane jest W
            'Zajęcia laboratoryjne': 'L',
            'Praktyka': 'P',
            'Seminarium': 'S',
            'Projekt': 'P',
            'Ćwiczenia': 'Ć'
        }[rodzajKursuTxt]           # Co sprawdzamy w Case
        #print 'TOJESTTO' + dzieciprowadzacyIPkt[len(dzieciprowadzacyIPkt)-1].string.strip() + 'TAAK'
        if(dzieciprowadzacyIPkt[len(dzieciprowadzacyIPkt)-1].string.strip() != ''):
            punktyECTS = dzieciprowadzacyIPkt[len(dzieciprowadzacyIPkt)-1].string.strip()
            if punktyECTS.find(',') != -1:
                punktyECTS = punktyECTS[:punktyECTS.index(',')]         # Czasami te punkty sa zapisane jako np. 3,00 więc pozbywamy się tej reszty :D
        else:
            punktyECTS = '0'    # W przypadku kiedy nie ma podane ECTS
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
        imieProw = imieNazwProw[dlLisProw-2]        #Odczytanie imienia
        nazwiskoProw = imieNazwProw[dlLisProw-1]    #Odczytanie nazwiska
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
        
        
        for dm in dataMiejsce:
            miejsce = ""
            dzien = ""
            parz = ""
            godzR = None
            godzZ = None
            g = models.Grupa()         # obiekt bazy tabeli Grupa
            pl = models.Plan()         # obiekt bazy tabeli Plan - GrupyStudentow
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
            g = models.Grupa.objects.get(kodGrupy = kodGrupyTxt, prowadzacy = prowadzacyGrupy, dzienTygodnia = dzien, parzystosc = parz,
                                                           godzinaOd = godzR, godzinaDo = godzZ, miejsce=miejsce, kurs = kursGrupy)
            #for g in grupy:
            if not(models.Plan.objects.filter(student = student, grupa = g).exists()):
                pl.student = student
                pl.grupa = g
                pl.save()

