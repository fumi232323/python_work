from django.test import TestCase

from datetime import date

from weather import testing


class TestWeather(TestCase):
    def test_date_display(self):
        target = testing.factory_weather(date=date(2017, 8, 11))
        self.assertEqual(target.date_display(), '08/11')

    def test_weekday_display(self):
        target = testing.factory_weather(date=date(2017, 8, 11))
        self.assertEqual(target.weekday_display(), '金')

    def test_chance_of_rain_display_normal(self):
        target = testing.factory_weather(chance_of_rain=50)
        self.assertEqual(target.chance_of_rain_display(), 50)

    def test_chance_of_rain_display_999(self):
        target = testing.factory_weather(chance_of_rain=999)
        self.assertEqual(target.chance_of_rain_display(), '---')


class TestHourlyWeather(TestCase):
    def test_chance_of_rain_display_normal(self):
        target = testing.factory_hourlyweather(chance_of_rain=30)
        self.assertEqual(target.chance_of_rain_display(), 30)

    def test_chance_of_rain_display_999(self):
        target = testing.factory_hourlyweather(chance_of_rain=999)
        self.assertEqual(target.chance_of_rain_display(), '---')

    def test_chance_of_rain_display_none(self):
        target = testing.factory_hourlyweather(chance_of_rain=None)
        self.assertEqual(target.chance_of_rain_display(), '---')
