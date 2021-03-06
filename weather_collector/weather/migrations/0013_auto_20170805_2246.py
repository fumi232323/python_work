# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-05 13:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weather', '0012_auto_20170805_1445'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weather',
            name='wind_speed',
            field=models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='風速（m/s）'),
        ),
    ]
