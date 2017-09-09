# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-24 06:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0047_auto_20170624_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='goldlog',
            name='store',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='user.Stores', verbose_name='充值店铺'),
            preserve_default=False,
        ),
    ]