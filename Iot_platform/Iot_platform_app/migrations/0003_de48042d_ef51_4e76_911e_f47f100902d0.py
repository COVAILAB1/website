# Generated by Django 4.2.4 on 2023-08-22 06:24

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Iot_platform_app', '0002_bddda48d_f63f_4b5f_bacc_c278202b1e00'),
    ]

    operations = [
        migrations.CreateModel(
            name='de48042d-ef51-4e76-911e-f47f100902d0',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('common_field_1', models.DateTimeField(default=datetime.datetime.now)),
                ('common_field_2', models.IntegerField()),
            ],
            options={
                'db_table': 'de48042d-ef51-4e76-911e-f47f100902d0',
            },
        ),
    ]
