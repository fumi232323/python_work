# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-21 10:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0018_auto_20170817_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='area',
            name='name',
            field=models.CharField(max_length=200, verbose_name='地域'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='name',
            field=models.PositiveIntegerField(choices=[(0, 'Yahoo!天気'), (1, 'ウェザーニュース'), (2, '日本気象協会 tenki.jp')], default=0, verbose_name='チャンネル'),
        ),
        migrations.AlterField(
            model_name='channel',
            name='weather_type',
            field=models.PositiveIntegerField(choices=[(0, '週間天気'), (1, '今日の天気')], verbose_name='予報タイプ'),
        ),
    ]
