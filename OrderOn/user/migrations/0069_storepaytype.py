# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-08 06:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0068_auto_20170706_2204'),
    ]

    operations = [
        migrations.CreateModel(
            name='StorePayType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cash', models.BooleanField(default=True, verbose_name='现金支付')),
                ('point', models.BooleanField(default=True, verbose_name='会员点')),
                ('gold', models.BooleanField(default=True, verbose_name='金币')),
                ('third_party', models.BooleanField(default=True, verbose_name='第三方平台')),
                ('alipay', models.BooleanField(default=True, verbose_name='支付宝')),
                ('store', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='user.Stores', verbose_name='店铺')),
            ],
            options={
                'verbose_name': '店铺支付方式',
                'verbose_name_plural': '店铺支付方式',
            },
        ),
    ]
