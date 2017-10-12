# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-10 21:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0003_auto_20171010_2101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='key',
            name='email',
            field=models.EmailField(default=None, help_text='E-mail of the person with whom the space is shared', max_length=254),
        ),
        migrations.AlterField(
            model_name='key',
            name='space_allotted',
            field=models.BigIntegerField(default=4096, help_text='Space you want to share in BYTES'),
        ),
    ]