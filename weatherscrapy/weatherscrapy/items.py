# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WeatherscrapyItem(scrapy.Item):
    channel = scrapy.Field()

    date = scrapy.Field()
    weather = scrapy.Field()
    highest_temperatures = scrapy.Field()
    lowest_temperatures = scrapy.Field()
    chance_of_rain = scrapy.Field()
    wind_speed = scrapy.Field()

    acquisition_date = scrapy.Field()


class HourlyWeatherscrapyItem(scrapy.Item):
    channel = scrapy.Field()

    date = scrapy.Field()
    time = scrapy.Field()
    weather = scrapy.Field()
    temperatures = scrapy.Field()
    humidity = scrapy.Field()
    precipitation = scrapy.Field()
    chance_of_rains = scrapy.Field()
    wind_direction = scrapy.Field()
    wind_speed = scrapy.Field()

    acquisition_date = scrapy.Field()
