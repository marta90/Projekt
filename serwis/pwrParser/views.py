from BeautifulSoup import BeautifulSoup, NavigableString, Tag   #parser kodu html
from serwis.zpi import models
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
import time, datetime
import re
from django.db import transaction
from django.db.models.signals import post_save
from twill import commands
from django.core.exceptions import ObjectDoesNotExist

from serwis.zpi import views


import unittest, time, re


# Create your views here.
def generujPlan(request):
    if request.method == 'POST':
        user = request.POST['userPWR']
        password = request.POST['passPWR']
        html = pobierzPlan(user, password)      # Funkcja zwracajaca kod html kursow
        if (html == "no"):
            return HttpResponse("no")
        if (html == "Bledne dane logowania"):
            return HttpResponse("Bledne dane logowania")
        if (html == "Zalogowany w innej sesji"):
            return HttpResponse("Zalogowany w innej sesji")
        else:
            for h in html:
                #html = open('C:\Projekt\serwis\pwrParser\zapis.htm').read()
                parser = BeautifulSoup(''.join(h))
                text = ''       #Wypisuje jesli nic nie ma
                for i in parser.findAll('tr'):
                    # tabelaA - tabela zapisow normalnych, tabelaB - tabela zapisow administracyjnych
                    tabelaA = i.findChildren('a', {'name': re.compile('^hrefZapisaneGrupySluchaczaTabela\d{7}$')}, False) #False wskazuje ze rekursja jest wylaczona
                    tabelaB = i.findChildren('a', {'name': re.compile('^hrefZapisaneAdminGrupySluchaczaTabela\d{7}$')}, False) #False wskazuje ze rekursja jest wylaczona
                    if len(tabelaA) > 0:    # Jesli sa jakies zapisy
                        zapisyAdministracyjne(request, i, tabelaA[0])
                    if len(tabelaB) >0:
                        zapisyAdministracyjne(request, i, tabelaB[0])
    else:
        text = 'Nic nie ma'
    request.session['content'] = 'timetable2'
    #return HttpResponseRedirect('/')
    return HttpResponse('yes')

# WYLOGOWANIE NA KONIEC
def pobierzPlan(user, password):
    tablicaHTMLow = []
    commands.add_extra_header('User-agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6')
    commands.clear_cookies()        # Czyszczenie ciastek
    commands.reset_browser()        #restart przegladarki
    commands.reset_output()
    #commands.config('use_BeautifulSoup', '0')
    commands.go("https://edukacja.pwr.wroc.pl/EdukacjaWeb/studia.do")   # Przechodzimy do edukacji
    
    commands.showlinks()            # DO USUNIECIA! Pokazuje linki

    commands.formclear('1')                                 # Czysci formularz logowania
    commands.formvalue('1', 'login', user)                  # Podaje login
    commands.formvalue('1', 'password', password)           # Podaje hasło
    commands.submit('0')                                    # Klika zaloguj
    
    print("Linki po submit")                                # DO USUNIECIA! Pokazuje informacje
    commands.showlinks()                                    # DO USUNIECIA! Pokazuje linki
    
    czyBledneLogowanie = sprawdzCzyBledneLogowanie(commands.show())                  # Sprawdza czy na stronie wystapil blad
    czyLogowanieWInnejSesji = sprawdzCzyLogowanieWInnejSesji(commands.show())
    if (czyBledneLogowanie == True):
        return "Bledne dane logowania"
    if (czyLogowanieWInnejSesji == True):
        return "zalogowany w innej sesji"
    commands.follow("zapisy.do")                               # Przechodzi linkiem na stronę zapisów
    
    # DO USUNIECIA! Pokazuje stronę po kliknięciu zapisy!
    print("Co po kliknieciu Zapisy")
    #commands.show()
    commands.showlinks()
    print "Forms:"
    formsy = commands.showforms()


    links = commands.showlinks()                            # Pobiera linki z danej strony 
    control = None
    values = None
    select_options = None
    control = commands.browser.get_form("1").find_control('ineSluId', type="select")
    
    if(control != None):                                    # Jesli na stronie jest select
        values = pobierzElementySelect(commands.show())     # Pobieram parserem wartosci selecta
        select_options = utworzTabeleSelect(values)         # Tworze nowy select podmieniajac stary
        select_attrs = {'id': 'some_id'}                    # Tworze atrybuty nowego selecta
        for v in values:                                    # Lece petla po wartosciach selecta
            form = commands.get_browser().get_form("1")                                     # Pobieram formularz
            ct = commands.browser.get_form("1").find_control('ineSluId', type="select")     # Pobieram kontrolke z selectem
            add_select_to_form(form, 'ineSluId', select_attrs, select_options)              # Tworze nowego selecta
            form.fixup()                                                                    # Sprawdzam czy cos nowego nie zostało dodanego do form
            commands.showforms()
            
            commands.formvalue("1", ct.name, v.strip())                                     # Podaje wartosc dla selecta
            commands.submit('0')                                                            # Klikam submit
            html = pobierzZajecia(commands)                                                 # Pobieram zajecia
            commands.follow("zapisy.do")                                                    # Wracam do strony zapisów
            
            #commands.sleep(6)
            if (html != "skreslony z kierunku"):            # Jesli funkcja zwrocila ze jest ktos skreslony to nie dodaje htmlu
                tablicaHTMLow.append(html)                  # Jeli nie zwrocila takiego komunikatu to dodajemy ten html do tablicy
    else:
        html = pobierzZajecia(commands)                     # Jesli nie ma selecta to pobieramy zajeci z tego kierunku i juz :D
        if (html != "skreslony z kierunku"):
            tablicaHTMLow.append(html)
            
    #print control.name, control.value, control.type
    #item = control.get("172748")
    #print item.name, item.selected, item.id, item.attrs
    
    #new_options
    #commands.formclear('1')
    #
    #
    #form = commands.get_browser().get_form("1")
    #
    #print('TO JEST TEN FORM:')
    #print(form)
    #print(len(form.controls))
    #
    #notIsSelect = True
    
    #for ct in form.controls:
    #    #print(ct)
    #    if ct.name == 'ineSluId':
    #        notIsSelect = False
    #        print('JESTEM')
    #        commands.sleep(3)
    #        
    #        select_attrs = {'id': 'some_id'}
    #        values = pobierzElementySelect(commands.show())
    #        select_options = utworzTabeleSelect(values)
    #        print(values)
    #        print(select_options)
    #        
    #        
    #        for v in values:
    #            #form.fixup()
    #            add_select_to_form(form, 'ineSluId', select_attrs, select_options)
    #            form.fixup()
    #            #ct.get(v).selected = True
    #            print(ct)
    #            print(form)
    #            print(v)
    #            commands.showforms()
    #            
    #            commands.formvalue("1", ct.name, v.strip())            # Podaje login
    #            print("JEEDEFE")
    #            commands.submit('0')
    #            html = pobierzZajecia(commands)
    #            commands.follow("zapisy.do")
    #            print("JEEEEEEEEESSSSSTTTTTEEEEEMMM")
    #            
    #            commands.sleep(6)
    #            if (html != "skreslony z kierunku"):
    #                tablicaHTMLow.append(html)
                #ct.get(v).selected = False
                
                
                
                
            
            #for ct2 in form.controls:
            #    if ct2.type == 'submit':                                             # szukam wsrod niej tej co ma typ submit
            #        commands.get_browser().clicked(form, ct2.attrs['name'])      # klikam na ten przycisk
            #        commands.get_browser().submit()
            
            #links = commands.showlinks()
            #commands.back()
            #commands.showforms()
            

            #return "no"

    #if (notIsSelect == True):
    #    html = pobierzZajecia(commands)
    #    if (html != "skreslony z kierunku"):
    #        tablicaHTMLow.append(html)

    wyloguj(commands)
    commands.browser.clear_cookies()        #usuwanie ciasteczek
    commands.reset_browser()        #restart przegladarki
    commands.reset_output()

    return tablicaHTMLow

def add_select_to_form(form, name, attrs, options):
    """
    Add a <select>...</select> to a given mechanize.HTMLForm object.
   
    Args:
        form: A mechanize.HTMLForm object.
        name: The value for the 'name' attribute of the <select> element.
        attrs: Attributes dictionary for the <select> element.
        options:  list of tuples, one for each <option> element; each tuple is
            in the form (value, description, selected):
                value: the 'value' attribute of the element
                description: the text between <option> and </option>
                selected: a boolean (remember to add 'multiple' to attrs
                    if more than one option is selected).
   
    Returns:
        Nothing.
    """
    form.new_control('select', name, attrs={'__select': attrs})
    for idx, option in enumerate(options):
        value, description, selected = option
        new_attrs = {
            '__select': attrs,
            'value': value,
            'contents': description,
        }
    if selected:
        new_attrs['selected'] = 'selected'
    form.new_control('select', name, attrs=new_attrs, index=idx)

def wyloguj(commands):
    
    forms = commands.showforms()                            # Pobranie formularzy
    naszForm = None                                         # Zmienna do ktorej zapiszemy znaleziony przez nas form
    for form in forms:                                      # Petla po formualrzach
        if form.action == 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/logOutUser.do':     # Jesli akcja danego formularza przenosi do szczegolow
            naszForm = form                                 # To zapisujemy znaleziony formularz
    
    #print(naszForm)                                         # DO USUNIECIA! Wypisuje znaleziony formularz
    
    ctrl = naszForm.controls                                                # pobieram ze znalezionego formularza wszystkie kontrolki
    for ct in ctrl:
        if ct.type == 'submit':                                             # szukam wsrod niej tej co ma typ submit
            commands.get_browser().clicked(naszForm, ct.attrs['name'])      # klikam na ten przycisk
            commands.get_browser().submit()
    
def sprawdzCzyBledneLogowanie(html):
    parser = BeautifulSoup(''.join(html))
    czyBlad = parser.findAll(text=re.compile('Niepowodzenie logowania'))
    if (len(czyBlad) != 0):
        return True
    else:
        return False
    
def sprawdzCzyLogowanieWInnejSesji(html):
    parser = BeautifulSoup(''.join(html))
    czyBlad = parser.findAll(text=[re.compile('zalogowany w innej sesji'), re.compile('Konieczne jest ponowne zalogowanie')])
    if (len(czyBlad) != 0):
        return True
    else:
        return False

def pobierzElementySelect(html):
    parser = BeautifulSoup(''.join(html))
    tab = []
    optionsy = parser.findAll('option')
    for i in optionsy:
        tab.append(i['value'].strip())
    return tab

def utworzTabeleSelect(values):
    select_options = []
    for v in values:
        a = (v, v, False)
        select_options.append(a)
    return select_options

def pobierzZajecia(commands):
    print("Po wybraniu")
    links = commands.showlinks()                            # Pobiera linki z danej strony
    commands.showforms()
    # Szuka w linkach tego przenoszącego na odpowiedni semestr.
    dateToday = datetime.date.today()
    firstOctober = datetime.date(dateToday.year, 10, 1)
    
    if dateToday > firstOctober:                            # Jesli dzisiaj jest wiekszy niz 1 Pazdziernika
        #Semestr zimowy
        for link in links:
            ktory = 0
            if link.text=='' + str(dateToday.year) + '/' + str(dateToday.year+1) + '':  # Szukamy linka o tytule (rok/rok+1)
                ktory = ktory + 1
                if ktory == 1:                              # Znalazł!
                    commands.go(link.url)                   # Przechodzimy pod url'sa który się kryje pod tym rokiem
    else:
        #Semest letni
        for link in links:
            ktory = 0
            if link.text=='' + str(dateToday.year)+ '/' + str(dateToday.year+1) + '':   # Szukamy linka o tytule (rok/rok+1)
                ktory = ktory + 1
                if ktory == 2:                              # Znalazł!
                    commands.go(link.url)                   # Przechodzimy pod url'sa który się kryje pod tym rokiem
    
    # DO USUNIECIA! Pokazuje stronę po kliknięciu danego semestru!
    print("Co po kliknieciu semestru:")
    commands.showlinks()
    print "Forms:"
    commands.showforms()
    
    # Szuka w formularzach tego odpowiadającego za pokazanie zapisanych kursów.
    forms = commands.showforms()                            # Pobranie formularzy
    naszForm = None                                         # Zmienna do ktorej zapiszemy znaleziony przez nas form
    for form in forms:                                      # Petla po formualrzach
        if form.action == 'https://edukacja.pwr.wroc.pl/EdukacjaWeb/zapisy.do?href=#hrefZapisySzczSlu':     # Jesli akcja danego formularza przenosi do szczegolow
            naszForm = form                                 # To zapisujemy znaleziony formularz
    
    print(naszForm)                                         # DO USUNIECIA! Wypisuje znaleziony formularz
    if(naszForm != None):                                   # To znaczy ze znalazlo taki rok i ze jeszcze istnieje student na tym kierunku
        ctrl = naszForm.controls                                                # pobieram ze znalezionego formularza wszystkie kontrolki
        for ct in ctrl:
            if ct.type == 'submit':                                             # szukam wsrod niej tej co ma typ submit
                commands.get_browser().clicked(naszForm, ct.attrs['name'])      # klikam na ten przycisk
                commands.get_browser().submit()
    
        print("Co po kliknieciu szczegoly zajec")
        commands.showlinks()
        #commands.sleep(5)
        print "Forms:"
        #commands.showforms()
        content = commands.show()
        #content =""
        #commands.browser.clear_cookies()        #usuwanie ciasteczek
        
        #print('PRZZEEEEEENIOSLEM')
        #commands.sleep(5)
        return content
    else:
        #commands.follow("zapisy.do")
        #print('PRZZEEEEEENIOSLEM')
        return("skreslony z kierunku")

def zapisyAdministracyjne(request, pierwszyTRZPlanem, pierwszyAZLinkiem):
        czyKursZapisany = None
        czyProwadzacyZapisany = None
        k = models.Kurs()          # obiekt bazy tabeli Kurs
        g = models.Grupa()         # obiekt bazy tabeli Grupa
        p = models.Prowadzacy()    # obiekt bazy tabeli Prowadzacy
        pl = models.Plan()         # obiekt bazy tabeli Plan - GrupyStudentow
        uz = views.uzSesja(request)
        
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
        czyJestKurs = None
        try:
            czyJestKurs = models.Kurs.objects.get(kodKursu = kodKursuTxt)
        except ObjectDoesNotExist:
            print("Kurs doesn't exist.")
            
        if (czyJestKurs == None):
            k.nazwa = nazwaKursuTxt
            k.rodzaj = rodzajKursuTxtKrotki
            k.ects = punktyECTS
            k.kodKursu = kodKursuTxt
            czyKursZapisany = k.save()
        else:
            if (czyJestKurs.nazwa != nazwaKursuTxt):
                czyJestKurs.nazwa = nazwaKursuTxt
                czyJestKurs.save()
            if (czyJestKurs.rodzaj != rodzajKursuTxtKrotki):
                czyJestKurs.rodzaj = rodzajKursuTxtKrotki
                czyJestKurs.save()
            if (czyJestKurs.ects != punktyECTS):
                czyJestKurs.ects = punktyECTS
                czyJestKurs.save()
        
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
        #czyJestProw = models.Prowadzacy.objects.filter(imie = imieProw, nazwisko = nazwiskoProw, tytul = tytulProw)
        czyJestProw = None
        try:
            czyJestProw = models.Prowadzacy.objects.get(imie = imieProw, nazwisko = nazwiskoProw, tytul = tytulProw)
        except ObjectDoesNotExist:
            print("Prowadzacy doesn't exist.")
        
        if (czyJestProw == None):
            p.imie = imieProw
            p.nazwisko = nazwiskoProw
            p.tytul = tytulProw
            p.ktoWprowadzil = uz
            p.dataOstZmianyDanych =  datetime.date.today()
            p.ktoZmienilDane = uz
            czyProwadzacyZapisany = p.save()
        
        # GODZINY I MIEJSCE
        prowadzacyGrupy = models.Prowadzacy.objects.get(imie = imieProw, nazwisko = nazwiskoProw, tytul = tytulProw)
        kursGrupy = models.Kurs.objects.get(kodKursu = kodKursuTxt)
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
            czyData = None
            czyKursZaoczny = False
            
            listaDM = dm.string.split(',', 1)           # oddzielenie daty od miejsca
            if listaDM[0].strip() != "bez terminu":
                miejsce = listaDM[1][1:]                # pobranie miejsca
                listaDG = listaDM[0].split()            # odzielenie dnia od godziny
                dzienIParz = listaDG[0].split('/', 1)   # oddzielenie dnia od parzystosci
                if (len(dzienIParz) == 1):
                    dzien = dzienIParz[0]
                else:
                    dzien = dzienIParz[0]
                    parz = dzienIParz[1]
                #print(dzien)
                czyData = re.search('^(\d{2,4})-(\d{2})-(\d{2})$', dzien)   # Od daty zaczyna się dla zaocznych
                if (czyData == None):
                    godz = listaDG[1].split('-', 1) # oddzielenie godz rozp od zak
                    godzR = godz[0]           
                    godzZ = godz[1]
                    #zapis do bazy Grupy
                    #czyJestGrupa = models.Grupa.objects.filter(kodGrupy = kodGrupyTxt, prowadzacy = prowadzacyGrupy, dzienTygodnia = dzien, parzystosc = parz,
                    #                                           godzinaOd = godzR, godzinaDo = godzZ, miejsce=miejsce, kurs = kursGrupy)
                    czyJestGrupa = None
                    try:
                        czyJestGrupa = models.Grupa.objects.get(kodGrupy = kodGrupyTxt, dzienTygodnia = dzien)
                    except ObjectDoesNotExist:
                        print("Grupa doesn't exist.")
        
                    if( czyJestGrupa == None ):
                        g.kodGrupy = kodGrupyTxt
                        g.prowadzacy = prowadzacyGrupy
                        g.dzienTygodnia = dzien
                        g.parzystosc = parz
                        g.godzinaOd = godzR
                        g.godzinaDo = godzZ
                        g.miejsce = miejsce
                        g.kurs = kursGrupy
                        g.save(force_insert=True)
                    else:   #Aktualizacja grupy
                        if (czyJestGrupa.prowadzacy != prowadzacyGrupy):
                            czyJestGrupa.prowadzacy = prowadzacyGrupy
                            czyJestGrupa.save()
                        if (czyJestGrupa.dzienTygodnia != dzien):
                            czyJestGrupa.dzienTygodnia = dzien
                            czyJestGrupa.save()
                        if (czyJestGrupa.parzystosc != parz):
                            czyJestGrupa.parzystosc = parz
                            czyJestGrupa.save()
                        if (czyJestGrupa.godzinaOd != godzR):
                            czyJestGrupa.godzinaOd = godzR
                            czyJestGrupa.save()
                        if (czyJestGrupa.godzinaDo != godzZ):
                            czyJestGrupa.godzinaDo = godzZ
                            czyJestGrupa.save()
                        if (czyJestGrupa.miejsce != miejsce):
                            czyJestGrupa.miejsce = miejsce
                            czyJestGrupa.save()
                        if (czyJestGrupa.kurs != kursGrupy):
                            czyJestGrupa.kurs = kursGrupy
                            czyJestGrupa.save()
                else:
                    czyKursZaoczny = True
            else:
                czyJestGrupa = None
                try:
                    czyJestGrupa = models.Grupa.objects.get(kodGrupy = kodGrupyTxt, dzienTygodnia = dzien)
                except ObjectDoesNotExist:
                    print("Grupa doesn't exist.")
                if( czyJestGrupa == None ):
                    g.kodGrupy = kodGrupyTxt
                    g.prowadzacy = prowadzacyGrupy
                    g.dzienTygodnia = dzien
                    g.parzystosc = parz
                    g.miejsce = miejsce
                    g.kurs = kursGrupy
                    g.save(force_insert=True)
                else:
                    if (czyJestGrupa.prowadzacy != prowadzacyGrupy):
                        czyJestGrupa.prowadzacy = prowadzacyGrupy
                        czyJestGrupa.save()
                    if (czyJestGrupa.dzienTygodnia != dzien):
                        czyJestGrupa.dzienTygodnia = dzien
                        czyJestGrupa.save()
                    if (czyJestGrupa.parzystosc != parz):
                        czyJestGrupa.parzystosc = parz
                        czyJestGrupa.save()
                    if (czyJestGrupa.miejsce != miejsce):
                        czyJestGrupa.miejsce = miejsce
                        czyJestGrupa.save()
                    if (czyJestGrupa.kurs != kursGrupy):
                        czyJestGrupa.kurs = kursGrupy
                        czyJestGrupa.save()
        
            if not(czyKursZaoczny):
                # ZAPISANIE TYCH GRUP DO STUDENTA
                #student = models.Student.objects.get(uzytkownik = uz)
                g = models.Grupa.objects.get(kodGrupy = kodGrupyTxt, dzienTygodnia = dzien)
                if not(models.Plan.objects.filter(uzytkownik = uz, grupa = g).exists()):
                    pl.uzytkownik = uz
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

