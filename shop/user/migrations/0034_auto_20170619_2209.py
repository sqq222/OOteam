# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-19 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0033_auto_20170619_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='food',
            name='detail',
            field=models.TextField(blank=True, null=True, verbose_name='商品详情'),
        ),
        migrations.AlterField(
            model_name='food',
            name='desc',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='描述'),
        ),
    ]
