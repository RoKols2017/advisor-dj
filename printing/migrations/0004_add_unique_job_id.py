# Generated manually to add unique constraint to job_id

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('printing', '0003_alter_printevent_byte_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='printevent',
            name='job_id',
            field=models.CharField(db_index=True, max_length=64, unique=True, verbose_name='ID задания'),
        ),
    ]


