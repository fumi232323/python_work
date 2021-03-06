# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-02 05:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0007_hourlyweather_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hourlyweather',
            name='date',
        ),
        migrations.AddField(
            model_name='hourlyweather',
            name='hourly_weather',
            field=models.CharField(default='-', max_length=200, verbose_name='天気'),
        ),
        migrations.AlterField(
            model_name='hourlyweather',
            name='weather',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weather.Weather'),
        ),
    ]
