# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-02 04:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0005_delete_hourlyweather'),
    ]

    operations = [
        migrations.CreateModel(
            name='HourlyWeather',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.TimeField(default=django.utils.timezone.now, verbose_name='時')),
                ('weather', models.CharField(max_length=200, verbose_name='天気')),
                ('highest_temperatures', models.IntegerField(default=20, verbose_name='気温（℃）')),
                ('precipitation', models.IntegerField(default=0, verbose_name='降水量（mm/h）')),
                ('wind_direction', models.CharField(blank=True, max_length=200, verbose_name='風向')),
                ('wind_speed', models.IntegerField(blank=True, default=0, verbose_name='風速（m/s）')),
                ('acquisition_date', models.DateTimeField(auto_now=True, verbose_name='取得日時')),
            ],
        ),
    ]
