<<<<<<< HEAD
from django.db import models

# Create your models here.
=======
﻿from django.db import models

class Wydzial(models.Model):
    nazwa = models.CharField(max_length = 240)
    def __unicode__(self):
        return self.kodgrupy
    class Meta:
        db_table = u'Wydzial'
        verbose_name_plural = 'Wydzialy'

class Kierunek(models.Model):
    nazwa = models.CharField(max_length = 240)
    wydzial = models.ForeignKey(Wydzial)
    liczbaSemestrowInz = models.IntegerField()
    liczbaSemestrowMgr = models.IntegerField()
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'Kierunek'
        verbose_name_plural = 'Kierunki'

class Uzytkownik(models.Model):
    nick = models.CharField(max_length = 60)
    imie = models.CharField(max_length = 60)
    nazwisko = models.CharField(max_length = 80)
    haslo = models.CharField(max_length = 128)
    mail = models.CharField(max_length = 200)
    ktoWprowadzil = models.ForeignKey('self', related_name = 'uzytkownik_wprowadzil')
    dataUtworzenia = models.DateTimeField(auto_now_add = True)
    dataOstLogowania = models.DateTimeField()
    dataOstZmianyHasla = models.DateTimeField()
    dataOstZmianyDanych = models.DateTimeField()
    ktoZmienilDane = models.ForeignKey('self', related_name = 'uzytkownik_zmienil')
    ileMoichWydarzen = models.IntegerField(default = 7) #z ilu dni wprzód pokazywać
    poziomDostepu = models.IntegerField(default = 0)
    def __unicode__(self):
        return self.nick
    class Meta:
        db_table = u'Uzytkownik'
        verbose_name_plural = 'Uzytkownicy'
 
class Prowadzacy(models.Model):
    imie = models.CharField(max_length = 50)
    nazwisko = models.CharField(max_length = 80)
    tytul = models.CharField(max_length = 50)
    ktoWprowadzil = models.ForeignKey(Uzytkownik, related_name = 'prowadzacy_wprowadzil')
    dataUtworzenia = models.DateTimeField(auto_now_add = True)
    dataOstZmianyDanych = models.DateTimeField()
    ktoZmienilDane = models.ForeignKey(Uzytkownik, related_name = 'prowadzacy_zmienil')
    konflikt = models.BooleanField(default = False)
    def __unicode__(self):
        return u'%s %s %s' % (self.tytul, self.imie, self.nazwisko)
    class Meta:
        db_table = u'Prowadzacy'
        verbose_name_plural = 'Prowadzacy'

class Kurs(models.Model):
    nazwa = models.CharField(max_length = 240)
    rodzaj = models.CharField(max_length = 1)
    ects = models.IntegerField()
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'Kurs'
        verbose_name_plural = 'Kursy'

class Grupa(models.Model):
    kodGrupy = models.CharField(max_length = 15)
    prowadzacy = models.ForeignKey(Prowadzacy)
    dzienTygodnia = models.CharField(max_length = 15)
    parzystosc = models.CharField(max_length = 2)
    godzinaOd = models.TimeField(null = True)
    godzinaDo = models.TimeField(null = True)
    miejsce = models.CharField(max_length = 20)
    kurs = models.ForeignKey(Kurs)
    def __unicode__(self):
        return self.kodGrupy
    class Meta:
        db_table = u'Grupa'
        verbose_name_plural = 'Grupy'

class Student(models.Model):
    uzytkownik = models.ForeignKey(Uzytkownik)
    indeks = models.CharField(max_length = 10)
    grupa = models.ManyToManyField(Grupa, through='Plan')
    kierunek = models.ManyToManyField(Kierunek, through='KierunkiStudenta')
    czyAktywowano = models.BooleanField(default=False)
    rodzajStudiow = models.IntegerField() #1 - inz/lic, 2 - mgr
    def __unicode__(self):
        return self.indeks
    class Meta:
        db_table = u'Student'
        verbose_name_plural = 'Studenci'

class Plan(models.Model):
    student = models.ForeignKey(Student)
    grupa = models.ForeignKey(Grupa)
    class Meta:
        db_table = u'Plan'
        verbose_name_plural = 'Plany'

class KierunkiStudenta(models.Model):
    student = models.ForeignKey(Student)
    kierunek = models.ForeignKey(Kierunek)
    semestr = models.IntegerField()
    uprawnienia = models.IntegerField(default = 0)
    class Meta:
        db_table = u'KierunkiStudenta'
        verbose_name_plural = 'Kierunki studentow'

class Shoutbox(models.Model):
    uzytkownik = models.ForeignKey(Uzytkownik)
    tresc = models.CharField(max_length = 240)
    data = models.DateTimeField(auto_now_add = True)
    czyWazne = models.BooleanField(default = False)
    def __unicode__(self):
        return self.tresc
    class Meta:
        db_table = u'Shoutbox'
        verbose_name_plural = 'Shoutbox'

class Wydarzenie(models.Model):
    nazwa = models.CharField(max_length = 240)
    opis = models.CharField(max_length = 240)
    dataWydarzenia = models.DateField()
    godzinaOd = models.TimeField(null = True)
    godzinaDo = models.TimeField(null = True)
    dataDodaniaWyd = models.DateTimeField(auto_now_add = True)
    rodzajWydarzenia = models.IntegerField()
    grupa = models.ForeignKey(Grupa, blank=True, null=True, on_delete=models.SET_NULL)
    dodal = models.ForeignKey(Uzytkownik, related_name = 'wydarzenie_dodal')
    uzytkownik = models.ManyToManyField(Uzytkownik, through = 'Kalendarz')
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'Wydarzenie'
        verbose_name_plural = 'Wydarzenia'

class AktualneWydarzenie(models.Model):
    stare = models.ForeignKey(Wydarzenie, related_name = 'aktualneWydarzenie_stare')
    nowe = models.ForeignKey(Wydarzenie, related_name = 'aktualneWydarzenie_nowe')
    class Meta:
        db_table = u'AktualneWydarzenie'
        verbose_name_plural = 'Aktualne wydarzenia'

class NotatkaDoWydarzenia(models.Model):
    wydarzenie = models.ForeignKey(Wydarzenie)
    notatka = models.CharField(max_length = 240)
    class Meta:
        db_table = u'NotatkaDoWydarzenia'
        verbose_name_plural = 'Notatki do wydarzen'  

class Kalendarz(models.Model):
    uzytkownik = models.ForeignKey(Uzytkownik)
    wydarzenie = models.ForeignKey(Wydarzenie)
    opis = models.CharField(max_length = 240)
    class Meta:
        db_table = u'Kalendarz'
        verbose_name_plural = 'Kalendarze'       

class KategoriaMiejsca(models.Model):
    nazwa = models.CharField(max_length = 20)
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'KategoriaMiejsca'
        verbose_name_plural = 'Kategorie miejsc'

class Miejsce(models.Model):
    kategoria = models.ForeignKey(KategoriaMiejsca)
    nazwa = models.CharField(max_length = 40)
    adres = models.CharField(max_length = 80)
    godzinyOtwarcia = models.CharField(max_length = 180)
    telefon = models.CharField(max_length = 40)
    x = models.CharField(max_length = 40)
    y = models.CharField(max_length = 40)
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'Miejsce'
        verbose_name_plural = 'Miejsca'

class Konsultacje(models.Model):
    prowadzacy = models.ForeignKey(Prowadzacy)
    dzienTygodnia = models.CharField(max_length = 15)
    parzystosc = models.CharField(max_length = 2)
    godzinaOd = models.TimeField()
    godzinaDo = models.TimeField()
    budynek = models.ForeignKey(Miejsce)
    sala = models.CharField(max_length = 10)
    inneInformacje = models.CharField(max_length = 200)
    dataOstZmianyDanych = models.DateTimeField()
    ktoZmienilDane = models.ForeignKey(Uzytkownik)
    def __unicode__(self):
        return prowadzacy.unicode()
    class Meta:
        db_table = u'Konsultacje'
        verbose_name_plural = 'Konsultacje'
        
class Tydzien(models.Model):
    nrTygodnia = models.IntegerField()
    dataOd = models.DateField()
    dataDo = models.DateField()
    rokAkademicki = models.CharField(max_length = 9)
    semestr = models.IntegerField() #1 - letni, 2 - zimowy
    grupa = models.ManyToManyField(Grupa, through = 'NotatkaDoPlanu')
    def __unicode__(self):
        return self.ntTygodnia
    class Meta:
        db_table = u'Tydzien'
        verbose_name_plural = 'Tygodnie'

class ZmianaDat(models.Model):
    data = models.DateTimeField()
    tydzien = models.ForeignKey(Tydzien)
    nowyDzien = models.IntegerField()
    parzystosc = models.CharField(max_length = 2)
    class Meta:
        db_table = u'ZmianaDat'
        verbose_name_plural = 'Zmiany dat'    

class NotatkaDoPlanu(models.Model):
    grupa = models.ForeignKey(Grupa)
    tydzien = models.ForeignKey(Tydzien)
    notatka = models.CharField(max_length = 240)                
    class Meta:
        db_table = u'NotatkaDoPlanu'
        verbose_name_plural = 'Notatki do planu'
>>>>>>> Stworzono model oraz sql do generowania tabel
