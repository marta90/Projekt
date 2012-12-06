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


admin.site.register(Grupa)
admin.site.register(Student)
admin.site.register(Wydzial)
admin.site.register(Kierunek)
admin.site.register(Uzytkownik)
admin.site.register(Prowadzacy)
admin.site.register(Kurs)
admin.site.register(Plan)
admin.site.register(Shoutbox)
admin.site.register(AktualneWydarzenie)
admin.site.register(Wydarzenie)
admin.site.register(Kalendarz)
admin.site.register(KategoriaMiejsca)
admin.site.register(Miejsce)
admin.site.register(Konsultacje)
admin.site.register(Tydzien)
admin.site.register(ZmianaDat)
admin.site.register(NotatkaDoPlanu)