# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-24 02:23
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_auto_20170524_0858'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserve',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='创建时间'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='reserve',
            name='desc',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='备注'),
        ),
        migrations.AddField(
            model_name='reserve',
            name='name',
            field=models.CharField(default=1, max_length=50, verbose_name='昵称'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='reserve',
            name='desk',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.Desk', verbose_name='桌号'),
        ),
    ]
