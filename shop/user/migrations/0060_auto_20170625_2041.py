# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-25 12:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0059_remove_food_stock'),
    ]

    operations = [
        migrations.AlterField(
            model_name='meal',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meal_store', to='user.Stores', verbose_name='用餐店铺'),
        ),
    ]