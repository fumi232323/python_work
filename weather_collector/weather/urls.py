from django.conf.urls import url

from . import views

app_name = 'weather'
urlpatterns = [
    url(r'^$', views.select_area, name='select_area'),
    url(r'^weekly/(?P<area_id>\d+)/$', views.weekly_weather, name='weekly'),
    url(r'^daily/(?P<weather_id>\d+)/$', views.daily_weather, name='daily'),
]
