# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-20 08:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0035_auto_20170620_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='food',
            name='allergens',
            field=models.ManyToManyField(blank=True, to='user.Allergens', verbose_name='过敏物质'),
        ),
    ]