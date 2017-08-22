from django.conf.urls import url

from . import views

app_name = 'channel'
urlpatterns = [
    url(r'^$', views.channel_list, name='list'),
    url(r'^register/$', views.register_channel, name='register'),
    url(r'^register/area/$', views.register_area, name='area'),
    url(r'^update/(?P<channel_id>\d+)/$', views.update_channel, name='update'),
    url(r'^delete/(?P<channel_id>\d+)/$', views.delete_channel, name='delete'),
]
