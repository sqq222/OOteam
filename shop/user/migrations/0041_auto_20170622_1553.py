# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-22 07:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0040_auto_20170622_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queue',
            name='desk_category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.DeskCategory', verbose_name='桌位类型'),
        ),
    ]