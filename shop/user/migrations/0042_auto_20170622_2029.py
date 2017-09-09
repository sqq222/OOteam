# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-22 12:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0041_auto_20170622_1553'),
    ]

    operations = [
        migrations.CreateModel(
            name='GoldLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recharge_gold', models.IntegerField(verbose_name='充值金币')),
                ('current_gold', models.IntegerField(verbose_name='剩余金币')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='充值时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '金币充值',
                'verbose_name_plural': '金币充值',
            },
        ),
        migrations.CreateModel(
            name='StorePointLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recharge_point', models.IntegerField(verbose_name='充值会员点')),
                ('current_point', models.IntegerField(verbose_name='剩余会员点')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='充值时间')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user.Stores', verbose_name='门店')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '会员点充值',
                'verbose_name_plural': '会员点充值',
            },
        ),
        migrations.RemoveField(
            model_name='payinfo',
            name='pay_type',
        ),
        migrations.AddField(
            model_name='payinfo',
            name='alipay_pay',
            field=models.IntegerField(default=0, verbose_name='支付宝支付'),
        ),
        migrations.AddField(
            model_name='payinfo',
            name='card_pay',
            field=models.IntegerField(default=0, verbose_name='银行卡支付'),
        ),
        migrations.AddField(
            model_name='payinfo',
            name='gold_pay',
            field=models.IntegerField(default=0, verbose_name='金币支付'),
        ),
        migrations.AddField(
            model_name='payinfo',
            name='point_pay',
            field=models.IntegerField(default=0, verbose_name='会员点支付'),
        ),
        migrations.AlterField(
            model_name='payinfo',
            name='money',
            field=models.IntegerField(verbose_name='支付总额'),
        ),
    ]
