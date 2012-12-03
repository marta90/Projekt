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

class UzytkownikInline(admin.TabularInline):
    model = Uzytkownik
    extra = 1

class PlanInline(admin.TabularInline):
    model = Grupa.uzytkownik.through
    extra = 1
    inlines = [UzytkownikInline,]

    #raw_id_fields= ('uzytkownik',)
    
class UserProfileInline(admin.StackedInline):
    model = Plan
    filter_horizontal = ('uzytkownik',)
    



class GrupaAdmin(admin.ModelAdmin):
    list_display = ('kodGrupy', 'kurs', 'dzienTygodnia', 'godzinaOd', 'godzinaDo', 'parzystosc', 'miejsce', 'zapisanych')
    inlines = [PlanInline,]
    #raw_id_fields = ("uzytkownik")
    list_filter = ('dzienTygodnia',)
    search_fields = ['kodGrupy', 'kurs__nazwa']
    #filter_horizontal = ('uzytkownik',)



admin.site.register(Grupa, GrupaAdmin)
#admin.site.register(Student)
#admin.site.register(Wydzial)
#admin.site.register(Kierunek)
#admin.site.register(Uzytkownik)
#admin.site.register(Prowadzacy)
#admin.site.register(Kurs)
#admin.site.register(Plan)
#admin.site.register(Shoutbox)
#admin.site.register(AktualneWydarzenie)
#admin.site.register(Wydarzenie)
#admin.site.register(Kalendarz)
#admin.site.register(KategoriaMiejsca)
#admin.site.register(Miejsce)
#admin.site.register(Konsultacje)
#admin.site.register(Tydzien)
#admin.site.register(ZmianaDat)
#admin.site.register(NotatkaDoPlanu)