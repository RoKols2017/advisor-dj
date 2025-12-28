# Generated manually to add indexes on user_id and printer_id

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('printing', '0004_add_unique_job_id'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='printevent',
            index=models.Index(fields=['user', 'timestamp'], name='printing_pr_user_id_tim_idx'),
        ),
        migrations.AddIndex(
            model_name='printevent',
            index=models.Index(fields=['printer', 'timestamp'], name='printing_pr_printer_tim_idx'),
        ),
    ]






