# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-23 06:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0082_auto_20170722_2152'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='创建时间'),
            preserve_default=False,
        ),
    ]
