from django.test import TestCase
from django.core.urlresolvers import reverse
from django.http import Http404

from datetime import datetime

from weather import models
from weather import testing
from weather.models import Weather


class TestRegisterWeather(TestCase):
    def _getTarget(self):
        return reverse('weather:weekly')

    def test_get(self):
        pass
