# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-08-19 07:16
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0090_auto_20170819_1502'),
    ]

    operations = [
        migrations.AlterField(
            model_name='abstractuser',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.Stores', verbose_name='门店'),
        ),
    ]