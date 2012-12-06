from django.db import models
from django.db.models.signals import post_save

# Create your models here.

class Wydzial(models.Model):
    nazwa = models.CharField(max_length = 250)
    def __unicode__(self):
        return self.nazwa
    def numerWydzialu(self):
        return self.nazwa.split(' ')
    class Meta:
        db_table = u'Wydzial'
        verbose_name_plural = 'Wydzialy'

class Kierunek(models.Model):
    nazwa = models.CharField(max_length = 250)
    wydzial = models.ForeignKey(Wydzial)
    liczbaSemestrow1st = models.IntegerField()
    liczbaSemestrow2stPoInz = models.IntegerField()
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'Kierunek'
        verbose_name_plural = 'Kierunki'

class Uzytkownik(models.Model):
    nick = models.CharField(max_length = 250)
    imie = models.CharField(max_length = 250)
    nazwisko = models.CharField(max_length = 250)
    haslo = models.CharField(max_length = 250)
    mail = models.CharField(max_length = 250)
    ktoWprowadzil = models.ForeignKey('self', related_name = 'uzytkownik_wprowadzil', null = True)
    dataUtworzenia = models.DateTimeField(auto_now_add = True)
    dataOstLogowania = models.DateTimeField(null = True)
    dataOstZmianyHasla = models.DateTimeField(null = True)
    dataOstZmianyDanych = models.DateTimeField(null = True)
    ktoZmienilDane = models.ForeignKey('self', related_name = 'uzytkownik_zmienil', null = True)
    ileMoichWydarzen = models.IntegerField(default = 7) #z ilu dni wprzod pokazywac
    poziomDostepu = models.IntegerField(default = 0)
    czyAktywowano = models.BooleanField(default=False)
    aktywator = models.CharField(max_length = 250, null = True)
    domyslny = models.IntegerField(null = True)
    def __unicode__(self):
        return self.nick
    class Meta:
        db_table = u'Uzytkownik'
        verbose_name_plural = 'Uzytkownicy'
 
class Prowadzacy(models.Model):
    imie = models.CharField(max_length = 250)
    nazwisko = models.CharField(max_length = 250)
    tytul = models.CharField(max_length = 250)
    ktoWprowadzil = models.ForeignKey(Uzytkownik, related_name = 'prowadzacy_wprowadzil')
    dataUtworzenia = models.DateTimeField(auto_now_add = True)
    dataOstZmianyDanych = models.DateTimeField()
    ktoZmienilDane = models.ForeignKey(Uzytkownik, related_name = 'prowadzacy_zmienil')
    konflikt = models.BooleanField(default = False)
    def __unicode__(self):
        return u'%s %s, %s' % (self.nazwisko, self.imie, self.tytul)
    class Meta:
        db_table = u'Prowadzacy'
        verbose_name_plural = 'Prowadzacy'

class Kurs(models.Model):
    nazwa = models.CharField(max_length = 250)
    rodzaj = models.CharField(max_length = 1)       # L, W, S, P
    ects = models.IntegerField()
    kodKursu = models.CharField(max_length = 250)
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
    miejsce = models.CharField(max_length = 250)
    kurs = models.ForeignKey(Kurs)
    uzytkownik = models.ManyToManyField(Uzytkownik, through = 'Plan')
    def __unicode__(self):
        #return u'%s %s' % (self.kodGrupy, self.kurs.nazwa)
        return self.kodGrupy
    def zapisanych(self):
        return self.uzytkownik.all().count()
    class Meta:
        db_table = u'Grupa'
        verbose_name_plural = 'Grupy'

class Student(models.Model):
    uzytkownik = models.ForeignKey(Uzytkownik)
    indeks = models.CharField(max_length = 6)
    kierunek = models.ForeignKey(Kierunek)
    semestr = models.IntegerField()
    rodzajStudiow = models.IntegerField() #1 - inz/lic, 2 - mgr
    uprawnienia = models.IntegerField(default = 0)
    def __unicode__(self):
        return self.indeks
    class Meta:
        db_table = u'Student'
        verbose_name_plural = 'Studenci'

class Plan(models.Model):
    uzytkownik = models.ForeignKey(Uzytkownik)
    grupa = models.ForeignKey(Grupa)
    class Meta:
        db_table = u'GrupyStudentow'
        verbose_name_plural = 'Plany'

class Shoutbox(models.Model):
    student = models.ForeignKey(Student)
    tresc = models.CharField(max_length = 250)
    data = models.DateTimeField(auto_now_add = True)
    czyWazne = models.BooleanField(default = False)
    def __unicode__(self):
        return self.tresc
    class Meta:
        db_table = u'Shoutbox'
        verbose_name_plural = 'Shoutbox'

class Wydarzenie(models.Model):
    nazwa = models.CharField(max_length = 250)
    opis = models.CharField(max_length = 250)
    dataWydarzenia = models.DateField()
    godzinaOd = models.TimeField(null = True)
    godzinaDo = models.TimeField(null = True)
    dataDodaniaWyd = models.DateTimeField(auto_now_add = True)
    rodzajWydarzenia = models.IntegerField()    #1 - Ogolnouczelniane, 2 - Wydzialowe, 3 - Kierunkowe, 4 - Zajeciowe, 5 - Rocznikowe, 6 - Prywatne, 7 - Prywatno-publiczne
    grupa = models.ForeignKey(Grupa, blank=True, null=True, on_delete=models.SET_NULL)
    dodal = models.ForeignKey(Student, related_name = 'wydarzenie_dodal')
    uzytkownik = models.ManyToManyField(Uzytkownik, through = 'Kalendarz')
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'Wydarzenie'
        verbose_name_plural = 'Wydarzenia'

class AktualneWydarzenie(models.Model):
    stare = models.ForeignKey(Wydarzenie, related_name = 'aktualneWydarzenie_stare')
    nowe = models.ForeignKey(Wydarzenie, related_name = 'aktualneWydarzenie_nowe')
    #def __unicode__(self):
    #    return self.stare.nazwa
    class Meta:
        db_table = u'AktualneWydarzenie'
        verbose_name_plural = 'Aktualne wydarzenia'

class Kalendarz(models.Model):
    uzytkownik = models.ForeignKey(Uzytkownik)
    wydarzenie = models.ForeignKey(Wydarzenie)
    opis = models.CharField(max_length = 250)
    class Meta:
        db_table = u'Kalendarz'
        verbose_name_plural = 'Kalendarze'       

class KategoriaMiejsca(models.Model):
    nazwa = models.CharField(max_length = 250)
    def __unicode__(self):
        return self.nazwa
    class Meta:
        db_table = u'KategoriaMiejsca'
        verbose_name_plural = 'Kategorie miejsc'

class Miejsce(models.Model):
    kategoria = models.ForeignKey(KategoriaMiejsca)
    nazwa = models.CharField(max_length = 250)
    adres = models.CharField(max_length = 250)
    godzinyOtwarcia = models.CharField(max_length = 250)
    telefon = models.CharField(max_length = 250)
    x = models.CharField(max_length = 250)
    y = models.CharField(max_length = 250)
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
    sala = models.CharField(max_length = 250)
    inneInformacje = models.CharField(max_length = 250)
    dataOstZmianyDanych = models.DateTimeField()
    ktoZmienilDane = models.ForeignKey(Uzytkownik)
    #def __unicode__(self):
    #    return prowadzacy.unicode()
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
        return str(self.nrTygodnia)
    class Meta:
        db_table = u'Tydzien'
        verbose_name_plural = 'Tygodnie'

class ZmianaDat(models.Model):
    data = models.DateField()
    tydzien = models.ForeignKey(Tydzien)
    nowyDzien = models.IntegerField()   #8-wolne, 9-sesja
    parzystosc = models.CharField(max_length = 2)
    class Meta:
        db_table = u'ZmianaDat'
        verbose_name_plural = 'Zmiany dat'    

class NotatkaDoPlanu(models.Model):
    grupa = models.ForeignKey(Grupa)
    tydzien = models.ForeignKey(Tydzien)
    notatka = models.CharField(max_length = 250)
    dodal = models.ForeignKey(Uzytkownik)
    class Meta:
        db_table = u'NotatkaDoPlanu'
        verbose_name_plural = 'Notatki do planu'
