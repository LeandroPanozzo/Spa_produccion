# Generated by Django 5.0.8 on 2024-10-12 20:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sentirseBien', '0005_payment_appointment_alter_appointment_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
