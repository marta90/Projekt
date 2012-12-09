from django.contrib import admin
from serwis.zpi.models import Grupa
from serwis.zpi.models import Student
from serwis.zpi.models import Wydzial
from serwis.zpi.models import Kierunek
from serwis.zpi.models import Uzytkownik
from serwis.zpi.models import Prowadzacy
from serwis.zpi.models import Kurs
from serwis.zpi.models import Plan
from serwis.zpi.models import Shoutbox
from serwis.zpi.models import Wydarzenie
from serwis.zpi.models import AktualneWydarzenie
from serwis.zpi.models import Kalendarz
from serwis.zpi.models import KategoriaMiejsca
from serwis.zpi.models import Miejsce
from serwis.zpi.models import Konsultacje
from serwis.zpi.models import Tydzien
from serwis.zpi.models import ZmianaDat
from serwis.zpi.models import NotatkaDoPlanu



class PlanInline(admin.TabularInline):
    model = Grupa.uzytkownik.through
    extra = 1
    
class NotatkaDoPlanuInline(admin.TabularInline):
    model = NotatkaDoPlanu
    extra = 1
    
class GrupaAdmin(admin.ModelAdmin):
    list_display = ('kodGrupy', 'kurs', 'dzienTygodnia', 'godzinaOd', 'godzinaDo', 'parzystosc', 'miejsce', 'zapisanych')
    inlines = [PlanInline, NotatkaDoPlanuInline]
    list_filter = ('dzienTygodnia',)
    search_fields = ['kodGrupy', 'kurs__nazwa']
    ordering = ('kodGrupy',)
    
class StudentInline(admin.TabularInline):
    model = Student
    extra = 1

class UzytkownikAdmin(admin.ModelAdmin):
    list_display = ('nick', 'nazwisko', 'imie', 'mail', 'dataUtworzenia')
    search_fields = ['imie', 'nazwisko']
    inlines = [StudentInline,]
    ordering = ('nazwisko', 'imie', '-dataUtworzenia')


class ShoutBoxAdmin(admin.ModelAdmin):
    list_display = ('student', 'tresc', 'data', 'czyWazne')
    search_fields = ['tresc']
    list_filter = ('data',)
    ordering = ('-data',)
    
class ZmianaDatInline(admin.TabularInline):
    model = ZmianaDat
    extra = 1

class TydzienAdmin(admin.ModelAdmin):
    list_display = ('nrTygodnia', 'dataOd', 'dataDo', 'rokAkademicki', 'semestr')
    search_fields = ['dataOd', 'dataDo']
    ordering = ('nrTygodnia',)
    inlines = [ZmianaDatInline,]
    
class GrupaInline(admin.TabularInline):
    model = Grupa
    extra = 1
    
class KursAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'rodzaj', 'ects', 'kodKursu')
    inlines = [GrupaInline,]
    ordering = ('nazwa', 'rodzaj')
    search_fields = ['nazwa', 'kodKursu']

class KierunekInline(admin.TabularInline):
    model = Kierunek
    extra = 1

class WydzialAdmin(admin.ModelAdmin):
    list_display = ('nazwa',)
    inlines = [KierunekInline,]
    ordering = ('nazwa',)
    #search_fields = ['nazwa',]
    
class KalendarzInline(admin.TabularInline):
    model = Kalendarz
    extra = 1
    

class WydarzeniaAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'dataWydarzenia', 'godzinaOd', 'godzinaDo', 'rodzajWydarzenia', 'grupa')
    #inlines = [KalendarzInline, AktualneWydarzenieInline,]
    ordering = ('-dataWydarzenia', 'nazwa',)
    list_filter = ('dataWydarzenia',)

    
class KonsultacjeInline(admin.TabularInline):
    model = Konsultacje
    extra = 1

class ProwadzacyAdmin(admin.ModelAdmin):
    list_display = ('nazwisko', 'imie', 'tytul', 'dataUtworzenia', 'konflikt')
    search_fields = ['imie', 'nazwisko']
    #inlines = [StudentInline,]
    inlines = [GrupaInline, KonsultacjeInline]
    ordering = ('nazwisko', 'imie', '-dataUtworzenia')
    
class MiejscaAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'adres', 'godzinyOtwarcia', 'telefon', 'x', 'y')
    search_fields = ['nazwa', 'adres', 'telefon']
    #list_filter = ('godzinyOtwarcia',)
    #inlines = [GrupaInline, KonsultacjeInline]
    ordering = ('nazwa',)
    

admin.site.register(Grupa, GrupaAdmin)
#admin.site.register(Student)
admin.site.register(Wydzial, WydzialAdmin)
#admin.site.register(Kierunek)
admin.site.register(Uzytkownik, UzytkownikAdmin)
admin.site.register(Prowadzacy, ProwadzacyAdmin)
#admin.site.register(Kurs, KursAdmin)
#admin.site.register(Plan)
admin.site.register(Shoutbox, ShoutBoxAdmin)
#admin.site.register(AktualneWydarzenie, AktualneWydarzenieAdmin)
admin.site.register(Wydarzenie, WydarzeniaAdmin)
#admin.site.register(Kalendarz)
#admin.site.register(KategoriaMiejsca)
admin.site.register(Miejsce, MiejscaAdmin)
#admin.site.register(Konsultacje)
admin.site.register(Tydzien, TydzienAdmin)
#admin.site.register(ZmianaDat)
#admin.site.register(NotatkaDoPlanu)