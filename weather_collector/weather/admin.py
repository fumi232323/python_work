from django.contrib import admin
from .models import Area, Channel, Weather, HourlyWeather
# Register your models here.

admin.site.register(Area)
admin.site.register(Channel)
admin.site.register(Weather)
admin.site.register(HourlyWeather)