# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-26 15:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0060_auto_20170625_2041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storepointlog',
            name='pay_type',
            field=models.IntegerField(choices=[(0, '现金'), (1, '银行转帐'), (2, '退款'), (3, '消费')], default=0, verbose_name='支付方式'),
        ),
    ]
