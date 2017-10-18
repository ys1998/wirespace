# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-18 13:12
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('share', '0006_auto_20171018_1823'),
    ]

    operations = [
        migrations.AlterField(
            model_name='key',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2017, 10, 18, 13, 12, 13, 630569, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='key',
            name='email',
            field=models.EmailField(blank=True, help_text='E-mail of the person with whom the space is shared', max_length=254, null=True),
        ),
    ]
