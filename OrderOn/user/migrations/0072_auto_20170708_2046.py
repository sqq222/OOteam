# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-08 12:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0071_auto_20170708_1755'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order_food',
            name='food_spec',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_food_spec', to='user.FoodSpec', verbose_name='商品规格'),
        ),
    ]
