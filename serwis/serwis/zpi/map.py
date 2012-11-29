from serwis.zpi import models
from django.http import HttpResponse, HttpResponseRedirect

import time, datetime
import os
import string
import random
import re
from django.db.models import Q


from django.utils import simplejson
from serwis.zpi.mainFunctions import *


############### MAPA ######################################################################

# Zaladowanie strony map.html do diva na stronie glownej
def zaladujMape(request):
	
	#mDziekanaty = models.Miejsce.objects.filter(kategoria__nazwa = "dziekanat")
	#mKsera = models.Miejsce.objects.filter(kategoria__nazwa = "ksero")
	#mGastronomia = models.Miejsce.objects.filter(kategoria__nazwa = "gastronomia")
	kategorie = models.KategoriaMiejsca.objects.exclude(id = 1)
	miejsca = models.Miejsce.objects.all()
	
	
	
	
	return render_to_response('map.html', {'kategorie':kategorie, 'miejsca':miejsca})

