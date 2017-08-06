# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WeatherscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    area = scrapy.Field()
    channel = scrapy.Field()
    
    date = scrapy.Field()
    weather = scrapy.Field()
    highest_temperatures = scrapy.Field()
    lowest_temperatures = scrapy.Field()
    chance_of_rain = scrapy.Field()
    wind_speed = scrapy.Field()
    
    acquisition_date = scrapy.Field()
    
# class HourlyWeatherscrapyItem(scrapy.Item):
