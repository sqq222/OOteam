# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-24 14:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0049_auto_20170624_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='payinfo',
            name='money_pay',
            field=models.IntegerField(default=0, verbose_name='现金支付'),
        ),
        migrations.AlterField(
            model_name='payinfo',
            name='pay_type',
            field=models.IntegerField(choices=[(0, '线上支付'), (1, '线下支付'), (2, '线上+线下支付')], default=0, verbose_name='方式'),
        ),
    ]
