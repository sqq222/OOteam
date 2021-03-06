# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-24 06:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0046_delete_usertype'),
    ]

    operations = [
        migrations.CreateModel(
            name='StorePoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=10, verbose_name='会员点名称')),
                ('end_date', models.IntegerField(verbose_name='有效期(月)')),
                ('store', models.ManyToManyField(to='user.Stores', verbose_name='会员点可用店铺')),
            ],
            options={
                'verbose_name': '会员点',
                'verbose_name_plural': '会员点',
            },
        ),
        migrations.RemoveField(
            model_name='storepointlog',
            name='store',
        ),
        migrations.AddField(
            model_name='goldlog',
            name='pay_type',
            field=models.IntegerField(default=0, verbose_name='支付方式'),
        ),
        migrations.AddField(
            model_name='storepointlog',
            name='end_date',
            field=models.DateField(default=django.utils.timezone.now, verbose_name='到期时间'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='storepointlog',
            name='pay_type',
            field=models.IntegerField(default=0, verbose_name='支付方式'),
        ),
        migrations.AddField(
            model_name='storepointlog',
            name='point',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='user.StorePoint', verbose_name='门店'),
        ),
    ]
