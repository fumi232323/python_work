# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-21 10:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0019_auto_20170821_1939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='name',
            field=models.PositiveIntegerField(choices=[(0, 'Yahoo!天気'), (1, 'ウェザーニュース'), (2, '日本気象協会 tenki.jp')], verbose_name='チャンネル'),
        ),
    ]
