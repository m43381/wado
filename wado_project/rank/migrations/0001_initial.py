# Generated by Django 4.2.20 on 2025-05-28 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Rank',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.CharField(max_length=30, unique=True, verbose_name='Звание')),
            ],
            options={
                'verbose_name': 'Звание',
                'verbose_name_plural': 'Звания',
            },
        ),
    ]
