# Generated by Django 5.0.1 on 2024-03-17 08:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('like', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bannedword',
            name='type',
            field=models.CharField(choices=[('b', 'banned'), ('m', 'mask'), ('c', 'check')], default='b'),
        ),
    ]
